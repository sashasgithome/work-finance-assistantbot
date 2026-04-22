# File: process.py
# Description : handles main ordered chatbot logic and LLM interaction related to user financial queries

import os
import streamlit as st
import json
from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION 
class GeminiAgent:
    def __init__(self):
        self.name = "Gemini"
        self.model = "gemini-2.5-flash-lite"

        self.llm = ChatGoogleGenerativeAI(
            model=self.model,
            google_api_key=os.getenv("GOOGLE_API_KEY"),
        )

# --- PRE-STEP: INPUT QUERY VALIDATION
@st.cache_data
def validate_query(user_query, _model):
    """Checks if user input can be answered by the finance bot. Handles out-of-scope queries."""

    system_prompt = f"""

    CONTEXT:
    You are an 'Intelligent and Helpful Customer Assistant Bot' for a national bank in Indonesia. 
    Your assistant capabilities are limited to : counting amount of transactions, checking total spending, or listing any trasactions.
    Your customer sends a query : {user_query}

    TASK: 
    1. If query is within your capabilities, return the string "VALID" only.
    2. If query is related to finance/banking but outside your capabilities list, return a polite sentence clarifying your limitations.  
    3. If query is unrelated to finance/banking, return a polite sentence explaining your specific role as a finance assistant only.
    """

    response = _model.invoke(system_prompt).content.strip()
    return response

# --- STEP 1: DATA-QUERY GENERATION
@st.cache_data
def get_query_params(user_query, category_list, _model):
    """Translates user query in natural language into structured parameters for data filtering and retrieval."""

    system_prompt = f"""

    CONTEXT:
    Today is {datetime.now().strftime('%Y-%m-%d')}. You must convert the user query into a JSON object for filtering a pandas dataframe.
    CATEGORIES: {category_list}
    USER QUERY: {user_query}

    TASK: Translate the user query into the following parameters.
    - operation: one of "sum", "count", "max", or "list". 
    --- Example: "sum" for total spending, "count" for number of transactions.
    - category_id: The numerical Category ID from the CATEGORIES list, must be an integer. Choose closest related.
    - search_terms: A list of keywords to search for, must not be empty.
    --- if query not in English, adjust to English unless for institution / brand names.
    --- add terms from USER QUERY that relate to merchants, brands, or spending types.
    --- add RELEVANT words from the CATEGORIES list that definitely relates and can help answer user query. 
    - start_date: The start date in "YYYY-MM-DD" format, default to one year ago if not specified.
    - end_date: The end date in "YYYY-MM-DD" format, default to today if not specified.
    
    JSON SCHEMA (English language only):
    {{
        "operation": "sum" | "count" | "max" | "list",
        "category_id": int | null,
        "search_terms": [string] | [],
        "start_date": "YYYY-MM-DD",
        "end_date": "YYYY-MM-DD"
    }}
    """

    try:
        response = _model.invoke(system_prompt).content
        clean_json = response.replace('```json', '').replace('```', '').strip()
        
        # Fallback
        if not clean_json:
            return {"operation": "list", "category": "all"}
        return json.loads(clean_json)
        
    except json.JSONDecodeError:
        print("Failed to decode JSON from LLM")
        return {"operation": "list", "category": "all"}
    
    except Exception as e:
        print(f"API Error: {e}")
        return {"operation": "list", "category": "all"}

# --- STEP 2: RELEVANT DATA RETRIEVAL
def execute_query(user_name, user_lang, df, params):
    """Query execution to fetch relevant data after multi-step filtering process."""

    relevant_df = df.copy()
    
    # Filter by parameters in the order of category group, date range, then 'search terms'
    if params.get("category_id"):
        relevant_df = relevant_df[relevant_df['category_by_system'] == params['category_id']]
    
    if params.get("start_date") and params.get("end_date"):
        relevant_df = relevant_df[(relevant_df['trx_date'] >= params['start_date']) & (relevant_df['trx_date'] <= params['end_date'])]

    if params.get("search_terms"):
        pattern = '|'.join(params['search_terms'])
        
        # Search across subheader and notes
        text_mask = relevant_df['subheader'].str.contains(pattern, case=False, na=False) | \
                    relevant_df['notes'].str.contains(pattern, case=False, na=False) 
        relevant_df = relevant_df[text_mask]
    
    # Order relevant transactions data by most recent
    relevant_df = relevant_df.sort_values(by='trx_date', ascending=False)
    relevant_data_amount = len(relevant_df)

    # Retrieve context for relevant transactions, limit to 10 (that gets listed) if more are found
    selected_columns = ['trx_date', 'subheader', 'detail_information', 'notes', 'amount', 'debit_credit']
    available_cols = [col for col in selected_columns if col in relevant_df.columns]

    if relevant_data_amount > 10:
        recent_transactions = relevant_df[available_cols].head(10).to_dict(orient="records")
    recent_transactions = relevant_df[available_cols].to_dict(orient="records")

    # Return structured results
    return {
        "user_name": user_name,
        "user_lang": user_lang,
        "total_spend": relevant_df['amount'].sum(),
        "transaction_count": relevant_data_amount,
        "transaction_data": recent_transactions
    }

# --- STEP 3: ANSWER POLISHER
@st.cache_data
def generate_final_response(user_query, context, _model):
    """Answer-polishing process by feeding LLM with relevant data (as context) and original user query."""

    polisher_prompt = f"""
    You are an 'Intelligent Customer Assistant', a helpful and professional financial bot for customer named {context['user_name']}.
    
    USER QUERY: "{user_query}"
    
    INPUT DATA:
    - Total Amount: Rp {context['total_spend']:,}
    - Number of Transactions: {context['transaction_count']}
    - Recent Details: {context['transaction_data']}

    GOAL:
    1. Answer the user's question directly and clearly, in {context['user_lang']} language with professional yet friendly tone.
    2. Provide helpful insight only if you are sure, such as largest transactions or spending trends. If no data is found, politely inform.
    5. Always format currency in Rupiah.
    
    STRICT RULE: Only use INPUT DATA provided above. Do not hallucinate transactions.
    """
    
    response = _model.invoke(polisher_prompt).content.strip()
    return response