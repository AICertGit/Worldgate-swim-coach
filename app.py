import streamlit as st
import pandas as pd
import requests
import base64
import json

# --- GITHUB DATABASE SETTINGS ---
# Streamlit will use these to read/write to your repo
REPO = "Worldgate-swim-coach"
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
    if res.status_code == 200:
        file_data = res.json()
        content = base64.b64decode(file_data["content"]).decode("utf-8")
        # Convert CSV string to DataFrame
        from io import StringIO
        df = pd.read_csv(StringIO(content))
        return df, file_data["sha"]
    elif res.status_code == 404:
        # File doesn't exist yet, return empty DataFrame
        df = pd.DataFrame(columns=["Coach", "Date", "Time", "Status"])
        return df, None
    else:
        st.error(f"Failed to load data: {res.status_code}")
        return pd.DataFrame(columns=["Coach", "Date", "Time", "Status"]), None

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
    return res.status_code in [200, 201]

# --- APP UI ---
st.title("🏊‍♀️ Swim Coach Scheduler")

# Load existing bookings
df, sha = load_data()

# Admin Area to Add Timeslots
st.subheader("Add Available Timeslot")
with st.form("add_slot"):
    coach = st.text_input("Coach Name")
    date = st.date_input("Date")
    time = st.text_input("Time (e.g. 10:00 AM)")
    submit = st.form_submit_button("Add Slot")

    
    if submit and coach and time:
        new_row = pd.DataFrame([{
            "Coach": coach,
            "Date": str(date),
            "Time": time,
            "Status": "Available"
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        if save_data(df, sha):
            st.success("Slot added successfully!")
            st.rerun()
        else:
            st.error("Failed to save to GitHub.")

# Client Area to Book
st.subheader("Available Slots")
available_slots = df[df["Status"] == "Available"]

if available_slots.empty:
    st.info("No lessons currently available.")
else:
    for idx, row in available_slots.iterrows():
        col1, col2 = st.columns([3, 1])
        col1.write(f"**{row['Coach']}** - {row['Date']} at {row['Time']}")
        if col2.button("Book Now", key=f"book_{idx}"):
            df.at[idx, "Status"] = "Booked"
            if save_data(df, sha):
                st.balloons()
                st.success("Successfully Booked!")
                st.rerun()
            else:
                st.error("Booking failed to save.")

# Show current schedule (Admin view)
st.divider()
if st.checkbox("Show Entire Schedule"):
    st.dataframe(df)
