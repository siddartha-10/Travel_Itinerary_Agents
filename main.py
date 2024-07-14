import streamlit as st
from datetime import datetime

# Set the page configuration
st.set_page_config(
    page_title="Travel Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="auto",
)

# Title and introduction
st.title("✈️ Travel Planner 🏨")
st.markdown("""
Welcome to the Travel Planner! Provide your travel details in the sidebar, and we'll help you plan your trip.
""")

# Input form in sidebar
with st.sidebar.form("travel_form"):
    where_from = st.text_input("Where are you traveling from? 🌍", "")
    where_to = st.text_input("Where are you traveling to? 🏖️", "")
    hotel_details = st.text_input("Hotel Preferences 🏨", "")
    departure_date = st.date_input("Departure Date 📅", value=None)
    return_date = st.date_input("Return Date 📅", value=None)
    travel_preference = st.selectbox("Travel Preference ✈️", ["", "Flight", "Train", "Car", "Bus"])

    submitted = st.form_submit_button("Plan My Trip")

# Output in the center
if submitted:
    if not where_from:
        st.error("Please enter the 'Where from' field!")
    elif not where_to:
        st.error("Please enter the 'Where to' field!")
    elif not hotel_details:
        st.error("Please enter the 'Hotel Preferences' field!")
    elif not departure_date:
        st.error("Please enter the 'Departure Date' field!")
    elif not return_date:
        st.error("Please enter the 'Return Date' field!")
    elif not travel_preference or travel_preference == "":
        st.error("Please select a 'Travel Preference'!")
    else:
        st.markdown(f"""
        ## Your Travel Plan
        - **From:** {where_from}
        - **To:** {where_to}
        - **Hotel Preferences:** {hotel_details}
        - **Departure Date:** {departure_date.strftime('%B %d, %Y')}
        - **Return Date:** {return_date.strftime('%B %d, %Y')}
        - **Travel Preference:** {travel_preference}
        
        Safe travels and have a fantastic trip! 🌟
        """)