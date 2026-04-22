# File: prefilter.py 
# Description : includes standalone functions for data loading, filtering, and category generation (prior to chat interaction)

import pandas as pd
import streamlit as st
import json
from dotenv import load_dotenv

load_dotenv()

@st.cache_data
def load_data(filename):
    """Gets data of all customers' transactions into a pandas DataFrame. Also handles date parsing and column name cleaning."""

    df = pd.read_csv(filename, sep=';')
    df.columns = df.columns.str.strip().str.lower()
    
    if "trx_date" in df.columns:
        df["trx_date"] = pd.to_datetime(df["trx_date"])
    return df

def get_category_descriptors(df):
    """Retrieves all unique subheaders, notes, and detail information for every category ID found in a customer."""

    mapping_suggestions = []
    
    # Group by assigned system ID
    for cat_id, group in df.groupby('category_by_system'):
        
        # Get unique values 
        subheaders = group['subheader'].unique().tolist()
        notes = group['notes'].unique().tolist()
        details = group['detail_information'].unique().tolist()
        
        # Combine all into a small representative string for every ID
        sample_string = f"ID {cat_id}:\nSubheaders: {subheaders}\nNotes: {notes}\nDetails: {details}"
        mapping_suggestions.append(sample_string)
        
    return "\n\n".join(mapping_suggestions)

def get_custom_category_list(df, model):
    """Uses LLM to provide general theme word for each category, including major/common words/phrases found."""

    mapping_suggestions = get_category_descriptors(df)

    system_prompt = f"""
    CONTEXT:
    You are a Financial Data Analyst specializing in categorizing banking transaction patterns.
    There is a list of unique 'Subheaders', 'Notes', and 'Detail Information' grouped by a numerical 'Category ID'. 
    INPUT DATA: {mapping_suggestions}

    TASK:
    1. Identify one-word representing high-level spending theme for each Category ID (e.g., Dining, Groceries, Education).
    2. List most common merchants, brands, or keywords found in that category, maximum of 6.
    3. Return the results in a strict format below.

    FORMAT OF STRING OUTPUT SHOULD ONLY BE :
    [CATEGORY NUMBER] : [MAIN TOPIC] ([EXAMPLE1, EXAMPLE2, EXAMPLE3, EXAMPLE4, EXAMPLE5])

    EXAMPLE OUTPUT: 
    1 : Groceries (Indomaret, Alfamart, Carrefour, Giant, Superindo)
    2 : Dining (Starbucks, McDonalds, Pizza Hut, KFC, Burger King)
    """

    # Generate category list by LLM
    response = model.invoke(system_prompt).content.strip()
    return response

def filter_by_cif(df, cif_id):
    """Filters the main dataframe for a specific Customer ID."""

    filtered_df = df[df['cif'].astype(str) == str(cif_id)].copy()
    return filtered_df

def get_customer_details(cif_id, profile_df):
    """Fetches customer name and language preference from profile dataframe."""

    try:
        user_profile = profile_df[profile_df['cif'].astype(str) == str(cif_id)]
        if user_profile.empty:
            return "Valued Customer", "en" # Default fallbacks
        
        customer_name = user_profile['customer_name'].values[0]
        prefs_json = json.loads(user_profile['preferences'].values[0])
        language_pref = prefs_json.get("language", "en")
        return customer_name, language_pref
        
    except Exception as e:
        print(f"Error fetching profile: {e}")
        return "Valued Customer", "en"
