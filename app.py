import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Swim Coach Scheduler", page_icon="🏊‍♀️")
st.title("🏊‍♀️ Swim Coach Scheduler")

# Connect to your Google Sheet
conn = st.connection("gsheets", type=GSheetsConnection)

# Read the data from the sheet
schedule_df = conn.read(worksheet="Sheet1", ttl=0)

# Clean up any empty rows Google Sheets might add
schedule_df = schedule_df.dropna(how="all")

# Sidebar to switch views
role = st.sidebar.radio("Select View:", ["Coach", "Student/Family"])

# ---------------- COACH VIEW ----------------
if role == "Coach":
    st.header("Manage Availability")
    
    with st.form("add_slot"):
        date = st.date_input("Date")
        time = st.time_input("Time")
        coach_name = st.text_input("Coach Name (e.g., Coach Sarah)")
        submitted = st.form_submit_button("Add Timeslot")
        
        if submitted:
            # Included the 'Coach' column in the saved data
            new_data = pd.DataFrame([{"Date": str(date), "Time": str(time), "Coach": coach_name, "Status": "Available"}])
            updated_df = pd.concat([schedule_df, new_data], ignore_index=True)
            
            # Save it back to Google Sheets
            conn.update(worksheet="Sheet1", data=updated_df)
            st.success(f"Added timeslot for {date} at {time} with {coach_name}!")
            st.rerun()
            
    st.divider()
    st.subheader("Current Schedule Overview")
    st.dataframe(schedule_df, use_container_width=True)

# ---------------- USER VIEW ----------------
elif role == "Student/Family":
    st.header("Book a Lesson")
    
    if schedule_df.empty:
        st.info("No slots available yet.")
    else:
        # Filter to only show 'Available' slots
        available_slots = schedule_df[schedule_df["Status"] == "Available"]
        
        if available_slots.empty:
            st.info("No available slots right now. Check back soon!")
        else:
            # Display slots with a booking button
            for index, row in available_slots.iterrows():
                col1, col2, col3, col4 = st.columns([1.5, 1.5, 2, 1])
                col1.write(f"📅 **{row['Date']}**")
                col2.write(f"⏰ **{row['Time']}**")
                col3.write(f"🏊 **{row['Coach']}**")
                
                # When the user clicks book
                if col4.button("Book", key=f"book_{index}"):
                    schedule_df.at[index, "Status"] = "Booked"
                    
                    # Update the Google Sheet with the new 'Booked' status
                    conn.update(worksheet="Sheet1", data=schedule_df)
                    st.success("Lesson Booked successfully!")
                    st.rerun()
                    
    st.divider()
    st.subheader("Currently Booked Lessons")
    booked = schedule_df[schedule_df["Status"] == "Booked"]
    st.dataframe(booked, use_container_width=True)
