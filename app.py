import streamlit as st
import pandas as pd
import datetime
import uuid
from supabase import create_client, Client

# --- Page Configuration ---
st.set_page_config(page_title="Daily Sales Collection Form", layout="wide")

# --- Initialize Session State for Duplicate Prevention ---
if 'transaction_id' not in st.session_state:
    st.session_state.transaction_id = str(uuid.uuid4())

# We store the shop data in session state so it doesn't vanish when you interact with other widgets
if 'shop_data' not in st.session_state:
    # Starting with one empty row for dynamic entry
    st.session_state.shop_data = pd.DataFrame([{"Shop ID": "", "Amount Deposited": 0.0}])

def clear_form():
    """Resets the transaction ID and form data after success"""
    st.session_state.transaction_id = str(uuid.uuid4())
    st.session_state.shop_data = pd.DataFrame([{"Shop ID": "", "Amount Deposited": 0.0}])
    st.rerun()

# --- Supabase Connection Function ---
def save_to_supabase(date, exec_id, route, cash, credit, total, table_df, txn_id):
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        supabase: Client = create_client(url, key)
        
        # Prepare data list
        data_to_insert = []
        for index, row in table_df.iterrows():
            entry = {
                "transaction_id": txn_id, # Prevents duplicates
                "date": str(date),
                "executive_id": exec_id,
                "route_name": route,
                "cash_amount": cash,
                "credit_amount": credit,
                "total_declared": total,
                "shop_id": int(row["Shop ID"]),
                "amount_deposited": float(row["Amount Deposited"])
            }
            data_to_insert.append(entry)
            
        # Insert data into the 'SalesData' table
        response = supabase.table("SalesData").insert(data_to_insert).execute()
        return True
    except Exception as e:
        if "unique constraint" in str(e):
             st.error("Error: This entry has already been submitted.")
        else:
             st.error(f"Error saving to Supabase: {e}")
        return False

st.title("Daily Sales Collection Form")
st.caption(f"Transaction Ref: {st.session_state.transaction_id}")
st.markdown("---")

# ==========================================
# SECTION 1: HEADER DETAILS
# ==========================================

executive_ids_list = [
    "Select Executive ID",
    "660373-Ajith K", "660554-Abhilash N", "660235-Gireesh V", "660482-Joseph Sebastian",
    "660601-Shabeeb T", "660200-Vineeth K Sugathan", "660185-Abdul Salam PH",
    "660184-Aslam K kareem", "660203-Joby Jhony", "660199-Binto Mathew",
    "660477-Nandha Gopal", "660593-Musharaf PM", "660181-Manoj PK",
    "660400-Sandeep Kumar", "660597-Kiran V P", "660207-Sanju Mthewkutty",
    "660473-Renjith Rajendran", "660538-Faisal F", "660256-Sreerag JV",
    "660494-Pratheesh G", "660515-Harikrishnan S"
]

route_names_list = [
    "Select Route Name",
    "KV64-Kasaragod Route", "KV24-Irikoor Route", "KV29-Alakode Route", "KV73-Balussery Route",
    "KV66-Koyilandy Route", "KV65-Kanhangadu Route", "KV58-Kannur Route", "KV50-Chokli Route",
    "KV67-Kuttiady Route", "KV72-Kozhikode Route", "KV14-Ambalapuzha Route", "KV03-Cheruthoni",
    "KV02-Bharananganam", "KV11-Aroor Route", "KV57-Kumali Route", "KV44-Kothamangalam Route",
    "KV06-Erumeli", "KV25-Mundakayam Route", "KV55-Muvattupuzha Route", "KV34-Varapuzha Route",
    "KV04-Munnar", "KV32-Amballoor Route", "KV76-Edappal Route", "KV71-Palakkad Route",
    "KV16-Thanoor", "ER162-Pattambi", "KV20-Ollur Route", "KV61-Manjeri",
    "KV23-Mayanoor Route", "KV74-Karunagappally Route", "KV33-Charumoodu Route",
    "KV28-Pazhavagadi", "KV13-Kulathupuzha Route", "KV19-Omalloor Route",
    "KV46-Kazhakoottam Route", "KV05-Haripadu", "KV39-Aruvikara", "KV09-Ezhukon",
    "KV12-Kilimanoor Route", "KV21-Vatiyoorkavu", "KV78-Edappally Route Ot",
    "KV77-Edappally Route", "KV08-Pathanapuram"
]

col1, col2 = st.columns(2)

with col1:
    submission_date = st.date_input("1. Choose Date", datetime.date.today())
    route_name = st.selectbox("3. Route Name", route_names_list)

with col2:
    exec_id = st.selectbox("2. Sale Executive ID", executive_ids_list)
    
    # --- SPLIT INPUTS ---
    c1, c2 = st.columns(2)
    with c1:
        cash_deposited = st.number_input("Cash Sales Deposited", min_value=0.0, format="%.2f", step=100.0)
    with c2:
        credit_deposited = st.number_input("Credit Sales Deposited", min_value=0.0, format="%.2f", step=100.0)
    
    # Auto-calculate Total
    total_deposited = cash_deposited + credit_deposited
    st.metric("Total Deposited (Cash + Credit)", f"{total_deposited:,.2f}")

st.markdown("---")

# ==========================================
# SECTION 2: SHOP COLLECTION & VALIDATION
# ==========================================
st.subheader("Shop Collection Details (Credit Breakdown)")
st.info("Enter details below. The Total here must match 'Credit Sales Deposited'.")

# 1. Calculate the Live Total of the table
current_shop_total = pd.to_numeric(st.session_state.shop_data["Amount Deposited"], errors='coerce').sum()

# 2. Validation Logic
is_valid = False
match_col1, match_col2 = st.columns([2, 3])

with match_col1:
    st.markdown(f"**Current Shop Total:** :blue[{current_shop_total:,.2f}]")

with match_col2:
    if abs(current_shop_total - credit_deposited) < 0.01:
        st.success("✅ Balanced: Shop Total matches Credit Sales")
        is_valid = True
    else:
        diff = credit_deposited - current_shop_total
        st.error(f"❌ Mismatch: Difference of {diff:,.2f}")
        is_valid = False

# 3. Dynamic Data Editor
edited_df = st.data_editor(
    st.session_state.shop_data,
    column_config={
        "Shop ID": st.column_config.NumberColumn("Shop ID", min_value=1, step=1, format="%d", width="medium"),
        "Amount Deposited": st.column_config.NumberColumn("Amount Deposited", min_value=0.0, format="%.2f", step=0.01, width="medium"),
    },
    num_rows="dynamic", # Allows adding/deleting rows dynamically
    use_container_width=True,
    key="editor"
)

# Update session state with changes so they persist
st.session_state.shop_data = edited_df

st.markdown("---")

# ==========================================
# SECTION 3: SUBMISSION
# ==========================================

# Button is disabled if totals don't match
if st.button("Submit Collection Data", type="primary", disabled=not is_valid):
    errors = []
    if exec_id == executive_ids_list[0]: errors.append("Please select a valid Sale Executive ID.")
    if route_name == route_names_list[0]: errors.append("Please select a valid Route Name.")
    if total_deposited == 0: errors.append("Total Deposited cannot be zero.")

    # Clean Data
    clean_df = edited_df.copy()
    clean_df["Shop ID"] = pd.to_numeric(clean_df["Shop ID"], errors='coerce')
    clean_df["Amount Deposited"] = pd.to_numeric(clean_df["Amount Deposited"], errors='coerce')
    submission_data = clean_df.dropna(subset=["Shop ID", "Amount Deposited"], how='any')

    if submission_data.empty: errors.append("Please enter at least one shop entry.")

    if errors:
        for err in errors: st.error(err)
    else:
        with st.spinner("Saving to Supabase Database..."):
            # Pass all new split fields and the transaction ID
            success = save_to_supabase(
                submission_date, 
                exec_id, 
                route_name, 
                cash_deposited, 
                credit_deposited, 
                total_deposited, 
                submission_data,
                st.session_state.transaction_id
            )
            
        if success:
            st.success("✅ Data Submitted Successfully!")
            st.balloons()
            clear_form() # Resets ID and clears table
