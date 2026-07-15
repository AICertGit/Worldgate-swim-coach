import streamlit as st
import pandas as pd
import requests
import base64
from io import StringIO

# --- GITHUB DATABASE SETTINGS ---
REPO = "worldgate-swim-coach"
FILE_PATH = "bookings.csv"

# Get GitHub credentials from Streamlit Secrets
try:
    GITHUB_TOKEN = st.secrets["github"]["token"]
    GITHUB_USER = st.secrets["github"]["username"]
except Exception:
    st.error("Missing GitHub credentials in Streamlit Secrets!")
    st.stop()

# Headers for GitHub API
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}
URL = f"https://api.github.com/repos/{GITHUB_USER}/{REPO}/contents/{FILE_PATH}"

# --- HELPER FUNCTIONS ---
def load_data():
    """Fetch bookings from GitHub CSV file"""
    res = requests.get(URL, headers=HEADERS)
    
    # Define our standard columns (Email added!)
    columns = ["Coach", "Date", "Time", "Status", "Client Name", "Client Phone", "Client Email"]
    
    if res.status_code == 200:
        file_data = res.json()
        content = base64.b64decode(file_data["content"]).decode("utf-8")
        
        # Read as string to prevent Pandas TypeError, then fill blank spaces
        df = pd.read_csv(StringIO(content), dtype=str)
        df = df.fillna("")
        
        # Smart Upgrade: Ensure all necessary columns exist even in older files
        for col in columns:
            if col not in df.columns:
                df[col] = ""
        return df, file_data["sha"]
        
    elif res.status_code == 404:
        return pd.DataFrame(columns=columns), None
    else:
        st.error(f"GitHub Error (Load): {res.status_code} - {res.text}")
        return pd.DataFrame(columns=columns), None

def save_data(df, sha=None):
    """Save bookings DataFrame back to GitHub CSV file"""
    csv_data = df.to_csv(index=False)
    encoded_content = base64.b64encode(csv_data.encode("utf-8")).decode("utf-8")
    
    payload = {
        "message": "Update bookings from App",
        "content": encoded_content
    }
    if sha:
        payload["sha"] = sha
        
    res = requests.put(URL, headers=HEADERS, json=payload)
    if res.status_code in [200, 201]:
        return True, ""
    else:
        return False, f"Code {res.status_code}: {res.text}"

# --- APP UI ---
st.title("🏊‍♀️ Swim Coach Scheduler")

# Load existing bookings
df, sha = load_data()

# --- ADMIN AREA: ADD TIMESLOTS ---
st.subheader("Add Available Timeslot")

time_options = [
    "7:00 AM", "7:30 AM", "8:00 AM", "8:30 AM", "9:00 AM", "9:30 AM", 
    "10:00 AM", "10:30 AM", "11:00 AM", "11:30 AM", "12:00 PM", "12:30 PM", 
    "1:00 PM", "1:30 PM", "2:00 PM", "2:30 PM", "3:00 PM", "3:30 PM", 
    "4:00 PM", "4:30 PM", "5:00 PM", "5:30 PM", "6:00 PM", "6:30 PM", 
    "7:00 PM", "7:30 PM"
]

with st.form("add_slot"):
    coach = st.text_input("Coach Name")
    date = st.date_input("Date")
    time = st.selectbox("Time Slot", options=time_options)
    submit = st.form_submit_button("Add Slot")
    
    if submit and coach:
        new_row = pd.DataFrame([{
            "Coach": coach,
            "Date": str(date),
            "Time": time,
            "Status": "Available",
            "Client Name": "",
            "Client Phone": "",
            "Client Email": ""
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        success, error_msg = save_data(df, sha)
        if success:
            st.success("Slot added successfully!")
            st.rerun()
        else:
            st.error(f"Failed to save to GitHub. Reason: {error_msg}")

# --- CLIENT AREA: VIEW & BOOK SLOTS ---
st.subheader("Available Slots")
available_slots = df[df["Status"] == "Available"]

if available_slots.empty:
    st.info("No lessons currently available.")
else:
    for idx, row in available_slots.iterrows():
        with st.expander(f"🟢 {row['Coach']} — {row['Date']} at {row['Time']}"):
            with st.form(key=f"book_form_{idx}"):
                client_name = st.text_input("Your Name", key=f"name_{idx}")
                client_phone = st.text_input("Your Phone Number", key=f"phone_{idx}")
                client_email = st.text_input("Your Email Address", key=f"email_{idx}")
                book_submit = st.form_submit_button("Confirm Booking")
                
                if book_submit:
                    # Require all three fields to be filled out
                    if not client_name or not client_phone or not client_email:
                        st.error("Please fill out your name, phone, and email to book.")
                    else:
                        df.at[idx, "Status"] = "Booked"
                        df.at[idx, "Client Name"] = client_name
                        df.at[idx, "Client Phone"] = client_phone
                        df.at[idx, "Client Email"] = client_email
                        
                        success, error_msg = save_data(df, sha)
                        if success:
                            st.balloons()
                            st.success("Successfully Booked!")
                            st.rerun()
                        else:
                            st.error(f"Booking failed. Reason: {error_msg}")

# --- ADMIN AREA: VIEW SCHEDULE ---
st.divider()
if st.checkbox("Show Schedule & Bookings (Admin View)"):
    st.write("### Complete Schedule Ledger")
    st.dataframe(df[["Coach", "Date", "Time", "Status", "Client Name", "Client Phone", "Client Email"]])

