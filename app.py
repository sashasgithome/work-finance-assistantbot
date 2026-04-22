# File: app.py 
# Description : shows streamlit UI, allows for input of CIP ID, displays chatbot --> allows for user interaction

import streamlit as st
from prefilter import load_data, filter_by_cif, get_custom_category_list, get_customer_details
from process import GeminiAgent, validate_query, get_query_params, execute_query, generate_final_response
from dotenv import load_dotenv

load_dotenv()

# --- INITIAL CONFIG
st.set_page_config(page_title="Finance Assistant Prototype", page_icon="🏦", layout="wide")
model = GeminiAgent().llm

# --- SIDEBAR: CIF LOGIN & CATEGORY VIEW
with st.sidebar:
    st.title("Customer Portal")
    
    # Get customer's unique CIF
    cif_id = st.text_input("Enter Customer Information File (CIF) ID:", placeholder="e.g., 123456")
    
    if cif_id:

        # Filter data for the specific user first
        raw_df = load_data("resources/transactions.csv")
        user_df = filter_by_cif(raw_df, cif_id)
        
        if user_df.empty:
            st.error(f"No transactions found for CIF ID {cif_id}.")
        else:
            st.success(f"CIF {cif_id} successfully verified.")

            # Retrieve customer name and language preference
            if "user_name" not in st.session_state or "user_lang" not in st.session_state:
                profile_df = load_data("resources/customer_profiles.csv")
                name, lang = get_customer_details(cif_id, profile_df)
                st.session_state.user_name = name
                st.session_state.user_lang = lang
    
            if st.session_state.user_lang == "id" : st.success(f"Selamat datang, {st.session_state.user_name}! Ada yang bisa saya bantu terkait keuangan Anda hari ini?") 
            else : st.success(f"Welcome, {st.session_state.user_name}! What financial insights can I assist you with today?")
            
            # Show system-made categories for the particular user
            if "category_list" not in st.session_state:
                if st.session_state.user_lang == "id" : text = f"Mohon tunggu sebentar. Sedang menganalisis pola pengeluaran dan transaksi CIF {cif_id}..."
                else : text = f"Please wait. Currently analyzing spending patterns of CIF {cif_id}..."

                with st.spinner(text):
                    cat_list = get_custom_category_list(user_df, model)
                    st.session_state.category_list = cat_list
                    st.session_state.current_cif = cif_id
                    st.session_state.user_df = user_df
            
            with st.expander("Finalized System Categorization", expanded=True):
                st.caption(f"Transactions of CIF ID {cif_id} have been categorized as the following:")
                st.text(st.session_state.category_list)
    else:
        st.error("Please enter valid CIF ID.")

    st.divider()
    if st.button("Reset Session"):
        st.session_state.messages = []
        st.rerun()

# --- MAIN UI: CHATBOT
st.title("🏦 Finance Assistant")

if not cif_id or user_df.empty:
    st.info("Please enter a valid CIF in the sidebar to access your financial insights.")
    st.stop()

# Show the chatbot interface
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask about your spending..."):

    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("Preparing your financial insights..."):

        # Validate the user query
        validation = validate_query(prompt, model)
        if validation != "VALID":
            full_response = validation

            with st.chat_message("assistant"):
                st.markdown(full_response)
                
        else:
            # Planner: Convert text to JSON using the identified categories
            params = get_query_params(prompt, st.session_state.category_list, model)
            
            # Executor: Filter the user_df based on LLM parameters
            context = execute_query(st.session_state.user_name, st.session_state.user_lang, st.session_state.user_df, params)
            
            # Polisher: Format the final response with context
            full_response = generate_final_response(prompt, context, model)
        
            # Assistant Response
            with st.chat_message("assistant"):
                st.markdown(full_response)
                
                with st.expander("SEE CHATBOT LOGIC DETAILS"):
                    st.write("**LLM Reasoning (JSON Params):**")
                    st.json(params)
                    st.write(f"**Data Grounding:** Found {context['transaction_count']} transactions totaling Rp {context['total_spend']:,}")

                    if context['transaction_data']:
                        st.write("**Transactions given as LLM Context:**")
                        st.dataframe(
                            context['transaction_data'], 
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.info("No individual transaction records were found for this query.")
            
    st.session_state.messages.append({"role": "assistant", "content": full_response})
