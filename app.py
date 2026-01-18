import streamlit as st
import pandas as pd
import datetime
import uuid
from supabase import create_client, Client

# --- 1. CONFIGURATION & SETUP ---
st.set_page_config(page_title="Daily Sales Collection Form", layout="wide")

# Initialize Session State Variables
if 'transaction_id' not in st.session_state:
    st.session_state.transaction_id = str(uuid.uuid4())

if 'shop_data' not in st.session_state:
    # Start with a few empty rows for easier entry
    data = [{"Shop ID": None, "Amount Deposited": None} for _ in range(5)]
    st.session_state.shop_data = pd.DataFrame(data)

def clear_form():
    """Resets the form and generates a new ID to prevent duplicates"""
    st.session_state.transaction_id = str(uuid.uuid4())
    # Reset table to empty state
    data = [{"Shop ID": None, "Amount Deposited": None} for _ in range(5)]
    st.session_state.shop_data = pd.DataFrame(data)
    # Rerun to refresh the UI immediately
    st.rerun()

# --- 2. SUPABASE FUNCTION ---
def save_to_supabase(date, exec_id, route, cash, credit, total, table_df, txn_id):
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        supabase: Client = create_client(url, key)
        
        # Prepare list of rows to insert
        data_to_insert = []
        for index, row in table_df.iterrows():
            entry = {
                "transaction_id": txn_id,
                "date": str(date),
                "executive_id": exec_id,
                "route_name": route,
                # --- VERIFIED UPDATES: CORRECT COLUMN NAMES ---
                "cash_amount_collected": float(cash),
                "credit_amount_collected": float(credit),
                # ----------------------------------------------
                "total_declared": float(total),
                "shop_id": int(row["Shop ID"]),
                "amount_deposited": float(row["Amount Deposited"])
            }
            data_to_insert.append(entry)
            
        # Perform Insert
        response = supabase.table("SalesData").insert(data_to_insert).execute()
        return True
    
    except Exception as e:
        if "unique constraint" in str(e).lower():
             st.error("Error: This transaction has already been recorded.")
        else:
             st.error(f"Database Error: {e}")
        return False

# --- 3. UI LAYOUT ---
st.title("Daily Sales Collection Form")
st.caption(f"Session Ref: {st.session_state.transaction_id}")
st.markdown("---")

# LISTS
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

# TOP FORM
col1, col2 = st.columns(2)
with col1:
    submission_date = st.date_input("1. Choose Date", datetime.date.today())
    route_name = st.selectbox("3. Route Name", route_names_list)

with col2:
    exec_id = st.selectbox("2. Sale Executive ID", executive_ids_list)
    
    # Split Cash/Credit
    c_sub1, c_sub2 = st.columns(2)
    with c_sub1:
        cash_deposited = st.number_input("Cash Deposited", min_value=0.0, step=100.0)
    with c_sub2:
        credit_deposited = st.number_input("Credit Deposited", min_value=0.0, step=100.0)
    
    total_deposited = cash_deposited + credit_deposited
    st.metric("Total Deposited", f"{total_deposited:,.2f}")

st.markdown("---")

# SHOP DETAILS & VALIDATION
st.subheader("Shop Collection (Credit Breakdown)")
st.info("The sum of Shop Amounts below MUST equal the 'Credit Deposited' value above.")

# Clean up data for calculation (handle None/NaN)
calc_df = st.session_state.shop_data.copy()
calc_df["Amount Deposited"] = pd.to_numeric(calc_df["Amount Deposited"], errors='coerce').fillna(0)
current_shop_total = calc_df["Amount Deposited"].sum()

# Validation Display
v_col1, v_col2 = st.columns([2, 3])
is_valid = False

with v_col1:
    st.write(f"**Shop Total:** {current_shop_total:,.2f}")

with v_col2:
    diff = credit_deposited - current_shop_total
    if abs(diff) < 0.01:
        st.success("✅ MATCHED")
        is_valid = True
    else:
        st.error(f"❌ MISMATCH: Difference is {diff:,.2f}")
        is_valid = False

# Editable Table
edited_df = st.data_editor(
    st.session_state.shop_data,
    column_config={
        "Shop ID": st.column_config.NumberColumn("Shop ID", min_value=1, format="%d"),
        "Amount Deposited": st.column_config.NumberColumn("Amount Deposited", min_value=0.0, format="%.2f"),
    },
    num_rows="dynamic",
    use_container_width=True,
    key="shop_editor"
)

# Sync edits back to session state
st.session_state.shop_data = edited_df

st.markdown("---")

# --- 4. SUBMIT LOGIC ---
if st.button("Submit Data", type="primary", disabled=not is_valid):
    # Basic Checks
    errors = []
    if exec_id == "Select Executive ID": errors.append("Select an Executive.")
    if route_name == "Select Route Name": errors.append("Select a Route.")
    if total_deposited == 0: errors.append("Total amount cannot be zero.")

    # Data Cleaning
    final_df = edited_df.copy()
    final_df["Shop ID"] = pd.to_numeric(final_df["Shop ID"], errors='coerce')
    final_df["Amount Deposited"] = pd.to_numeric(final_df["Amount Deposited"], errors='coerce')
    # Remove empty rows
    final_df = final_df.dropna(subset=["Shop ID", "Amount Deposited"])
    
    if final_df.empty and credit_deposited > 0:
        errors.append("You entered Credit Sales but listed no shops.")

    if errors:
        for e in errors: st.error(e)
    else:
        with st.spinner("Saving..."):
            success = save_to_supabase(
                submission_date, exec_id, route_name, 
                cash_deposited, credit_deposited, total_deposited,
                final_df, st.session_state.transaction_id
            )
            
            if success:
                st.success("✅ Data Submitted Successfully!")
                st.balloons()
                clear_form()
