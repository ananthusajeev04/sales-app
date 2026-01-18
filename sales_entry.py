import streamlit as st
import pandas as pd
import datetime
import uuid
import time
from supabase import create_client, Client

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Sales Entry", layout="wide")

# Initialize Session State
if 'transaction_id' not in st.session_state:
    st.session_state.transaction_id = str(uuid.uuid4())

# Initialize Table Data
if 'shop_data' not in st.session_state:
    # Start with 5 empty rows
    st.session_state.shop_data = pd.DataFrame(
        [{"Shop ID": None, "Amount Deposited": None} for _ in range(5)]
    )

def clear_form_data():
    """Reset data and generate new ID"""
    st.session_state.transaction_id = str(uuid.uuid4())
    st.session_state.shop_data = pd.DataFrame(
        [{"Shop ID": None, "Amount Deposited": None} for _ in range(5)]
    )

# --- 2. DATABASE FUNCTION ---
def save_to_supabase(date, exec_id, route, cash, credit, total, table_df, txn_id):
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        supabase: Client = create_client(url, key)
        
        data_to_insert = []
        for index, row in table_df.iterrows():
            entry = {
                "transaction_id": txn_id,
                "date": str(date),
                "executive_id": exec_id,
                "route_name": route,
                "cash_amount_collected": float(cash),
                "credit_amount_collected": float(credit),
                "total_declared": float(total),
                "shop_id": int(row["Shop ID"]),
                "amount_deposited": float(row["Amount Deposited"])
            }
            data_to_insert.append(entry)
            
        supabase.table("SalesData").insert(data_to_insert).execute()
        return True
    except Exception as e:
        if "unique constraint" in str(e).lower():
             st.error("Error: This transaction has already been recorded.")
        else:
             st.error(f"Database Error: {e}")
        return False

# --- 3. UI: TOP SECTION (Live Updates) ---
st.title("Daily Sales Entry")
st.caption(f"Ref: {st.session_state.transaction_id}")

executive_ids_list = [
    "Select Executive ID", "660373-Ajith K", "660554-Abhilash N", "660235-Gireesh V", "660482-Joseph Sebastian",
    "660601-Shabeeb T", "660200-Vineeth K Sugathan", "660185-Abdul Salam PH", "660184-Aslam K kareem",
    "660203-Joby Jhony", "660199-Binto Mathew", "660477-Nandha Gopal", "660593-Musharaf PM", "660181-Manoj PK",
    "660400-Sandeep Kumar", "660597-Kiran V P", "660207-Sanju Mthewkutty", "660473-Renjith Rajendran",
    "660538-Faisal F", "660256-Sreerag JV", "660494-Pratheesh G", "660515-Harikrishnan S"
]
route_names_list = [
    "Select Route Name", "KV64-Kasaragod Route", "KV24-Irikoor Route", "KV29-Alakode Route", "KV73-Balussery Route",
    "KV66-Koyilandy Route", "KV65-Kanhangadu Route", "KV58-Kannur Route", "KV50-Chokli Route",
    "KV67-Kuttiady Route", "KV72-Kozhikode Route", "KV14-Ambalapuzha Route", "KV03-Cheruthoni",
    "KV02-Bharananganam", "KV11-Aroor Route", "KV57-Kumali Route", "KV44-Kothamangalam Route",
    "KV06-Erumeli", "KV25-Mundakayam Route", "KV55-Muvattupuzha Route", "KV34-Varapuzha Route",
    "KV04-Munnar", "KV32-Amballoor Route", "KV76-Edappal Route", "KV71-Palakkad Route",
    "KV16-Thanoor", "ER162-Pattambi", "KV20-Ollur Route", "KV61-Manjeri", "KV23-Mayanoor Route",
    "KV74-Karunagappally Route", "KV33-Charumoodu Route", "KV28-Pazhavagadi", "KV13-Kulathupuzha Route",
    "KV19-Omalloor Route", "KV46-Kazhakoottam Route", "KV05-Haripadu", "KV39-Aruvikara", "KV09-Ezhukon",
    "KV12-Kilimanoor Route", "KV21-Vatiyoorkavu", "KV78-Edappally Route Ot", "KV77-Edappally Route",
    "KV08-Pathanapuram"
]

# Inputs outside the form so they update instantly
c1, c2 = st.columns(2)
with c1:
    submission_date = st.date_input("Date", datetime.date.today())
    route_name = st.selectbox("Route Name", route_names_list)
with c2:
    exec_id = st.selectbox("Executive ID", executive_ids_list)
    
    sc1, sc2 = st.columns(2)
    with sc1:
        cash_deposited = st.number_input("Cash Collected", min_value=0.0, step=100.0)
    with sc2:
        credit_deposited = st.number_input("Credit Collected", min_value=0.0, step=100.0)

total_deposited = cash_deposited + credit_deposited

st.markdown("---")

# --- 4. UI: THE FORM (Stops Auto-Reload) ---
st.subheader("Shop Collection Details")
st.info("Enter all shops below. The app will NOT reload while you type.")

with st.form("entry_form", clear_on_submit=False):
    # The Table
    # We use st.session_state.shop_data as the starting point
    edited_df = st.data_editor(
        st.session_state.shop_data,
        column_config={
            "Shop ID": st.column_config.NumberColumn("Shop ID", min_value=1, format="%d"),
            "Amount Deposited": st.column_config.NumberColumn("Amount Deposited", min_value=0.0, format="%.2f"),
        },
        num_rows="dynamic",
        use_container_width=True
    )
    
    # The Submit Button
    submitted = st.form_submit_button("Verify & Submit Entry", type="primary")

    if submitted:
        # --- VALIDATION LOGIC ---
        # 1. Clean Data
        clean_df = edited_df.dropna(subset=["Shop ID", "Amount Deposited"], how='any')
        current_shop_total = clean_df["Amount Deposited"].sum()
        
        # 2. Check Math
        diff = credit_deposited - current_shop_total
        is_valid = False
        
        if exec_id == "Select Executive ID":
            st.error("⚠️ Please select an Executive ID.")
        elif route_name == "Select Route Name":
            st.error("⚠️ Please select a Route Name.")
        elif total_deposited <= 0:
            st.error("⚠️ Total Amount cannot be zero.")
        elif credit_deposited > 0 and clean_df.empty:
            st.error("⚠️ You entered Credit Sales but the Shop list is empty.")
        elif abs(diff) > 0.01:
            st.error(f"❌ MISMATCH: Credit is {credit_deposited:,.2f} but Shop Total is {current_shop_total:,.2f}. Diff: {diff:,.2f}")
        else:
            is_valid = True
            
        # 3. Save if Valid
        if is_valid:
            with st.spinner("Saving data..."):
                success = save_to_supabase(
                    submission_date, exec_id, route_name, 
                    cash_deposited, credit_deposited, total_deposited,
                    clean_df, st.session_state.transaction_id
                )
                
                if success:
                    st.success("✅ Saved Successfully!")
                    st.balloons()
                    time.sleep(2)
                    # Clear data and Reload
                    clear_form_data()
                    st.rerun()
