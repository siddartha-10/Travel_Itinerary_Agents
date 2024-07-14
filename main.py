import streamlit as st
from datetime import datetime
from dotenv import load_dotenv
import os
load_dotenv()
from langgraph.graph import StateGraph, END, START
from typing import Annotated, TypedDict, List
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, AnyMessage
import requests
import json
from tavily import TavilyClient

model = AzureChatOpenAI(openai_api_version=os.environ.get("AZURE_OPENAI_VERSION", "2023-07-01-preview"),
    azure_deployment=os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt4chat"),
    azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT", "https://gpt-4-trails.openai.azure.com/"),
    api_key=os.environ.get("AZURE_OPENAI_KEY"),
    temperature=0.3)

tavily = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))

from langchain_core.pydantic_v1 import BaseModel
class Queries(BaseModel):
    queries: List[str]

class AgentState(TypedDict):
    Where_from: str
    Where_to: str
    Local_expert: str
    Hotel_details: str
    Hotel_expert: str
    Departure_date: str
    Return_date: str
    Travel_preference: str # This maybe by car, flight etc
    Travel_expert: str
    FINAL_DRAFT: str

LOCAL_EXPERT_QUERIES_PROMPT = """ You are an expert local guide of . \
You are living there for almost 15 years \
Your goal is to generate max of 2 queries such that it will retrieve overview of what \
the city has to offer, including hidden gems, cultural hotspots, must-visit landmarks,\
"""
LOCAL_EXPERT_PROMPT = """ Your goal is to share the most insightful and interesting details about this place. \
Use the context given below of the {city} to find about its attractions and \
customs to provide valuable information that will enrich the travel experience for visitors.\

example output:- 
1) Time's Square :- This is a great place to walk around at the night times. etc
......
"""

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