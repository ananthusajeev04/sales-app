import streamlit as st
import pandas as pd
import datetime
import uuid
import time
from supabase import create_client, Client

# --- 1. CONFIGURATION & STATE ---
st.set_page_config(page_title="Daily Sales Entry", layout="wide")

if 'transaction_id' not in st.session_state:
    st.session_state.transaction_id = str(uuid.uuid4())

# Initialize three separate DataFrames for the three tables
if 'prev_collection_df' not in st.session_state:
    st.session_state.prev_collection_df = pd.DataFrame([{"Shop ID": None, "Amount": None} for _ in range(5)])
if 'cheque_df' not in st.session_state:
    st.session_state.cheque_df = pd.DataFrame([{"Shop ID": None, "Amount": None} for _ in range(5)])
if 'cash_not_deposited_df' not in st.session_state:
    st.session_state.cash_not_deposited_df = pd.DataFrame([{"Shop ID": None, "Amount": None} for _ in range(5)])

def clear_form_data():
    """Reset all data and generate a new transaction ID."""
    st.session_state.transaction_id = str(uuid.uuid4())
    st.session_state.prev_collection_df = pd.DataFrame([{"Shop ID": None, "Amount": None} for _ in range(5)])
    st.session_state.cheque_df = pd.DataFrame([{"Shop ID": None, "Amount": None} for _ in range(5)])
    st.session_state.cash_not_deposited_df = pd.DataFrame([{"Shop ID": None, "Amount": None} for _ in range(5)])
    st.rerun()

# --- 2. DATABASE SAVING FUNCTION ---
def save_to_supabase(date, exec_id, route, cash_sales, prev_coll, total_dep, cheque, cash_not, expense, prev_df, cheque_df, cash_not_df, txn_id):
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        supabase: Client = create_client(url, key)
        
        data_to_insert = []
        
        # Helper function to create a row payload
        def create_payload(deposit_type, shop_id, amount):
            return {
                "transaction_id": txn_id,
                "date": str(date),
                "executive_id": exec_id,
                "route_name": route,
                "cash_sales_deposited": float(cash_sales),
                "previous_collection_deposited": float(prev_coll),
                "total_deposited": float(total_dep),
                "cheque_deposited": float(cheque),
                "cash_not_deposited": float(cash_not),
                "total_expense": float(expense),
                "deposit_type": deposit_type,
                "shop_id": int(shop_id),
                "amount": float(amount)
            }

        # Process Table 1: Previous Collection
        for _, row in prev_df.iterrows():
            data_to_insert.append(create_payload('previous_collection', row["Shop ID"], row["Amount"]))
            
        # Process Table 2: Cheque Deposited
        for _, row in cheque_df.iterrows():
            data_to_insert.append(create_payload('cheque', row["Shop ID"], row["Amount"]))
            
        # Process Table 3: Cash Not Deposited
        for _, row in cash_not_df.iterrows():
            data_to_insert.append(create_payload('cash_not_deposited', row["Shop ID"], row["Amount"]))
            
        # Perform a single batch insert
        if data_to_insert:
            supabase.table("SalesData").insert(data_to_insert).execute()
        return True
    except Exception as e:
        st.error(f"Database Error: {e}")
        return False

# --- 3. UI: HEADERS AND INPUTS ---
st.title("Daily Sales Entry")
st.caption(f"Transaction Ref: {st.session_state.transaction_id}")

executive_ids = ["Select Executive ID", "660373-Ajith K", "660554-Abhilash N", "660235-Gireesh V", "660482-Joseph Sebastian", "660601-Shabeeb T", "660200-Vineeth K Sugathan", "660185-Abdul Salam PH", "660184-Aslam K kareem", "660203-Joby Jhony", "660199-Binto Mathew", "660477-Nandha Gopal", "660593-Musharaf PM", "660181-Manoj PK", "660400-Sandeep Kumar", "660597-Kiran V P", "660207-Sanju Mthewkutty", "660473-Renjith Rajendran", "660538-Faisal F", "660256-Sreerag JV", "660494-Pratheesh G", "660515-Harikrishnan S"]
route_names = ["Select Route Name", "KV64-Kasaragod Route", "KV24-Irikoor Route", "KV29-Alakode Route", "KV73-Balussery Route", "KV66-Koyilandy Route", "KV65-Kanhangadu Route", "KV58-Kannur Route", "KV50-Chokli Route", "KV67-Kuttiady Route", "KV72-Kozhikode Route", "KV14-Ambalapuzha Route", "KV03-Cheruthoni", "KV02-Bharananganam", "KV11-Aroor Route", "KV57-Kumali Route", "KV44-Kothamangalam Route", "KV06-Erumeli", "KV25-Mundakayam Route", "KV55-Muvattupuzha Route", "KV34-Varapuzha Route", "KV04-Munnar", "KV32-Amballoor Route", "KV76-Edappal Route", "KV71-Palakkad Route", "KV16-Thanoor", "ER162-Pattambi", "KV20-Ollur Route", "KV61-Manjeri", "KV23-Mayanoor Route", "KV74-Karunagappally Route", "KV33-Charumoodu Route", "KV28-Pazhavagadi", "KV13-Kulathupuzha Route", "KV19-Omalloor Route", "KV46-Kazhakoottam Route", "KV05-Haripadu", "KV39-Aruvikara", "KV09-Ezhukon", "KV12-Kilimanoor Route", "KV21-Vatiyoorkavu", "KV78-Edappally Route Ot", "KV77-Edappally Route", "KV08-Pathanapuram"]

c1, c2, c3 = st.columns(3)
with c1: submission_date = st.date_input("Date", datetime.date.today())
with c2: route_name = st.selectbox("Route Name", route_names)
with c3: exec_id = st.selectbox("Executive ID", executive_ids)

st.markdown("---")

# Row 1: Main Deposits
md1, md2, md3 = st.columns(3)
with md1: cash_sales_deposited = st.number_input("Cash Sales Deposited", min_value=0.0, step=100.0)
with md2: prev_collection_deposited = st.number_input("Previous Collection Deposited", min_value=0.0, step=100.0)
with md3:
    total_deposited = cash_sales_deposited + prev_collection_deposited
    st.metric("Total Deposited", f"{total_deposited:,.2f}")

# Row 2: Other Inputs
od1, od2, od3 = st.columns(3)
with od1: cheque_deposited = st.number_input("Cheque Deposited", min_value=0.0, step=100.0)
with od2: cash_not_deposited = st.number_input("Cash not deposited on same day", min_value=0.0, step=100.0)
with od3: total_expense = st.number_input("Total Expense", min_value=0.0, step=10.0)

st.markdown("---")

# --- 4. UI: THREE SEPARATE TABLES ---

# Helper to configure columns
col_config = {
    "Shop ID": st.column_config.NumberColumn("Shop ID", min_value=1, format="%d"),
    "Amount": st.column_config.NumberColumn("Amount", min_value=0.0, format="%.2f")
}

# Table 1: Previous Collection Breakdown
st.subheader("1. Previous collection Deposit Breakdown")
st.info(f"Total must equal: {prev_collection_deposited:,.2f}")
st.session_state.prev_collection_df = st.data_editor(
    st.session_state.prev_collection_df, column_config=col_config, num_rows="dynamic", use_container_width=True, key="prev_coll_editor"
)

# Table 2: Cheque Deposited Breakdown
st.subheader("2. Cheque Deposited Breakdown")
st.info(f"Total must equal: {cheque_deposited:,.2f}")
st.session_state.cheque_df = st.data_editor(
    st.session_state.cheque_df, column_config=col_config, num_rows="dynamic", use_container_width=True, key="cheque_editor"
)

# Table 3: Cash Not Deposited Breakdown
st.subheader("3. Cash not deposited on same day Breakdown")
st.info(f"Total must equal: {cash_not_deposited:,.2f}")
st.session_state.cash_not_deposited_df = st.data_editor(
    st.session_state.cash_not_deposited_df, column_config=col_config, num_rows="dynamic", use_container_width=True, key="cash_not_editor"
)

st.markdown("---")

# --- 5. VALIDATION & SUBMISSION LOGIC ---
if st.button("Verify & Submit Entry", type="primary"):
    errors = []
    
    # Basic Checks
    if exec_id == "Select Executive ID": errors.append("⚠️ Select an Executive ID.")
    if route_name == "Select Route Name": errors.append("⚠️ Select a Route Name.")
    
    # Helper function to clean and sum a dataframe
    def get_clean_sum(df):
        clean = df.dropna(subset=["Shop ID", "Amount"], how='any')
        return clean, clean["Amount"].sum()

    # Validation 1: Previous Collection
    clean_prev_df, prev_sum = get_clean_sum(st.session_state.prev_collection_df)
    if abs(prev_sum - prev_collection_deposited) > 0.01:
        errors.append(f"❌ Table 1 Mismatch: Total is {prev_sum:,.2f}, expected {prev_collection_deposited:,.2f}.")
    elif prev_collection_deposited > 0 and clean_prev_df.empty:
        errors.append("⚠️ 'Previous Collection Deposited' has a value, but Table 1 is empty.")

    # Validation 2: Cheque Deposited
    clean_cheque_df, cheque_sum = get_clean_sum(st.session_state.cheque_df)
    if abs(cheque_sum - cheque_deposited) > 0.01:
        errors.append(f"❌ Table 2 Mismatch: Total is {cheque_sum:,.2f}, expected {cheque_deposited:,.2f}.")
    elif cheque_deposited > 0 and clean_cheque_df.empty:
        errors.append("⚠️ 'Cheque Deposited' has a value, but Table 2 is empty.")

    # Validation 3: Cash Not Deposited
    clean_cash_not_df, cash_not_sum = get_clean_sum(st.session_state.cash_not_deposited_df)
    if abs(cash_not_sum - cash_not_deposited) > 0.01:
        errors.append(f"❌ Table 3 Mismatch: Total is {cash_not_sum:,.2f}, expected {cash_not_deposited:,.2f}.")
    elif cash_not_deposited > 0 and clean_cash_not_df.empty:
        errors.append("⚠️ 'Cash not deposited' has a value, but Table 3 is empty.")

    # Final Processing
    if errors:
        for e in errors: st.error(e)
    else:
        with st.spinner("Saving data to Supabase..."):
            success = save_to_supabase(
                submission_date, exec_id, route_name,
                cash_sales_deposited, prev_collection_deposited, total_deposited,
                cheque_deposited, cash_not_deposited, total_expense,
                clean_prev_df, clean_cheque_df, clean_cash_not_df,
                st.session_state.transaction_id
            )
            if success:
                st.success("✅ Data Submitted Successfully!")
                st.balloons()
                time.sleep(2)
                clear_form_data()
