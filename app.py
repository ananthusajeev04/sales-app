import streamlit as st
import pandas as pd
import datetime
from supabase import create_client, Client

# --- Page Configuration ---
st.set_page_config(page_title="Daily Sales Collection Form", layout="wide")

# --- Supabase Connection Function ---
def save_to_supabase(date, exec_id, route, total_declared, table_df):
    try:
        # Load credentials from Streamlit Secrets
        # You will add these in the Streamlit Dashboard later
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        
        supabase: Client = create_client(url, key)
        
        # Prepare data list
        data_to_insert = []
        for index, row in table_df.iterrows():
            entry = {
                "date": str(date),
                "executive_id": exec_id,
                "route_name": route,
                "total_declared": total_declared,
                "shop_id": int(row["Shop ID"]),
                "amount_deposited": float(row["Amount Deposited"])
            }
            data_to_insert.append(entry)
            
        # Insert data into the 'SalesData' table
        response = supabase.table("SalesData").insert(data_to_insert).execute()
        return True
    except Exception as e:
        st.error(f"Error saving to Supabase: {e}")
        return False

st.title("Daily Sales Collection Form")
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
    total_deposited = st.number_input(
        "4. Total Amount Deposited (Total Cash Handoff)",
        min_value=0.0, format="%.2f", step=0.01
    )

st.markdown("---")

st.subheader("Shop Collection Details")
st.info("Enter details in the grid below. You can copy-paste data from Excel into this grid.")

num_rows = 40
data_structure = {
    "S.no": list(range(1, num_rows + 1)),
    "Shop ID": [pd.NA] * num_rows,
    "Amount Deposited": [pd.NA] * num_rows,
}

df_initial = pd.DataFrame(data_structure)

edited_df = st.data_editor(
    df_initial,
    column_config={
        "S.no": st.column_config.NumberColumn("S.no", disabled=True, width="small"),
        "Shop ID": st.column_config.NumberColumn("Shop ID", min_value=1, step=1, format="%d", width="medium"),
        "Amount Deposited": st.column_config.NumberColumn("Amount Deposited", min_value=0.0, format="%.2f", step=0.01, width="medium"),
    },
    hide_index=True, use_container_width=True, num_rows="fixed"
)

st.markdown("---")

if st.button("Submit Collection Data", type="primary"):
    errors = []
    if exec_id == executive_ids_list[0]: errors.append("Please select a valid Sale Executive ID.")
    if route_name == route_names_list[0]: errors.append("Please select a valid Route Name.")

    clean_df = edited_df.copy()
    clean_df["Shop ID"] = pd.to_numeric(clean_df["Shop ID"], errors='coerce')
    clean_df["Amount Deposited"] = pd.to_numeric(clean_df["Amount Deposited"], errors='coerce')
    submission_data = clean_df.dropna(subset=["Shop ID", "Amount Deposited"], how='all')
    submission_data = submission_data[submission_data["Shop ID"].notna() | submission_data["Amount Deposited"].notna()]

    if submission_data.empty: errors.append("Please enter at least one entry in the Shop Details table.")

    table_total = submission_data["Amount Deposited"].sum()
    if abs(table_total - total_deposited) > 0.01:
         st.warning(f"⚠️ Warning: Total declared ({total_deposited:.2f}) does not match table sum ({table_total:.2f}).")

    if errors:
        for err in errors: st.error(err)
    else:
        with st.spinner("Saving to Supabase Database..."):
            success = save_to_supabase(submission_date, exec_id, route_name, total_deposited, submission_data)
            
        if success:
            st.success("✅ Data Submitted Successfully!")
            st.balloons()
