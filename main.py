import streamlit as st
from dotenv import load_dotenv
import os
load_dotenv()
from langgraph.graph import StateGraph, END, START
from typing import Annotated, TypedDict, List
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain_core.pydantic_v1 import BaseModel
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, AnyMessage
import requests
import json
from tavily import TavilyClient

# model = AzureChatOpenAI(openai_api_version=os.environ.get("AZURE_OPENAI_VERSION", "2023-07-01-preview"),
#     azure_deployment=os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt4chat"),
#     azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT", "https://gpt-4-trails.openai.azure.com/"),
#     api_key=os.environ.get("AZURE_OPENAI_KEY"),
#     temperature=0.3)
model = ChatOpenAI(temperature=0.3, model='gpt-4o-mini')  # openai model
tavily = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY")) # tavily 

class Queries(BaseModel):  # This is class will help in storing all the queries generated
    queries: List[str]

class AgentState(TypedDict): # This is class stores the agentstates.
    Where_from: str
    Where_to: str
    Local_expert: str
    Hotel_details: str
    Hotel_expert: str
    Departure_date: str
    Return_date: str
    FINAL_DRAFT: str

########################################################################
# PROMPTS
########################################################################

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
HOTEL_EXPERT_QUERIES_PROMPT = """ 
Generate single search query to find the best hotels that fits the user preferences {user_preferences} in the {city} only. \
""" 
HOTEL_EXPERT_PROMPT = """ Your goal is to share the best hotels that fit the user preference. \
Use the context given below of the hotels and choose few hotels that better fit the user preference \
Also also give a single sentence reasoning, why is that hotel better. \

Here is the user preference, {hotels}

Include hotels in the {city}

example output:- 
1) Marriot :- This is hotel is a 5 start hotel which is luxury and it is near to many of the famous attractions. \
Per night cost would be:- 200$ per room. and also give the hotel location.
Important amenities:-
1) pool
2) spa .....etc
......
"""
TRAVEL_CONCIERGE_PROMPT = """
Expand this guide into a full travel
itinerary for this time  with detailed per-day plans, including
weather forecasts, places to eat, packing suggestions,
and a budget breakdown.

You MUST suggest actual places to visit, actual hotels
to stay and actual restaurants to go to.

This itinerary should cover all aspects of the trip,
from arrival to departure, integrating the city guide
information with practical travel logistics.

Your final answer MUST be a complete expanded travel plan,
formatted as markdown, encompassing a daily schedule,
anticipated weather conditions, recommended clothing and
items to pack, and a detailed budget, ensuring THE BEST
TRIP EVER, Be specific and give it a reason why you picked
# up each place, what make them special!

Do not assume, anything.

To calculate the duration the trip use the {departure_date} and {return_date}

Below are all the details about the places , hotels, and transportation. Do not assume that the\
user is going to stay at a hotel or take this flight given them after the Iternary as additional infroamtion.

Here are the local places and attractions {Local_expert}
Here are the hotels {Hotel_expert}

example:-

Day 1: Arrival and Exploring the City
Weather Forecast: ......
Morning:
Arrival from India to Miami via your selected flight option. (Travel Plan Option 1)
Check-in at the hotel
Afternoon:
Lunch at xyz restaurent
Explore Little Havana,
Evening:
Enjoy a stroll around the Art Deco
Dinner at xyz place

What to Pack: Swimwear, sunscreen, light clothing, comfortable walking shoes, a light rain jacket (just in case of showers), and a camera.

The example of Day 1 should continue for rest of the days and what to pack depends upon that days sechdule and where
we are going.

Hotels:-
1_ .....
2) ....

What to pack:-
1) ......
2) .....

"""

########################################################################
# AGENTS
########################################################################

def Local_expert_agent(state: AgentState):
    queries = model.with_structured_output(Queries).invoke([
        SystemMessage(content=LOCAL_EXPERT_QUERIES_PROMPT),
        HumanMessage(content = state['Where_to']),
    ])
    context = ""
    for q in queries.queries:
        print(q)
        response = tavily.search(query=q, max_results = 3, include_raw_content = True, include_domains = ["expedia.com"])
        for result in response['results']:
            context = "\n\n ".join(result['raw_content'])
    best_version = model.invoke([
        SystemMessage(content=LOCAL_EXPERT_PROMPT.format(city = state['Where_to'])),
        HumanMessage(content = context),
    ]).content
    return {"Local_expert": best_version}

def Hotel_expert_agent(state: AgentState):
    queries = model.with_structured_output(Queries).invoke([
        SystemMessage(content=HOTEL_EXPERT_QUERIES_PROMPT.format(city = state['Where_to'],
        user_preferences = state['Hotel_details'])),
        HumanMessage(content = "\n\n" + "Here is my preferences to finding a hotel "+ state['Hotel_details']),
    ])
    context = ""
    for q in queries.queries:
        print(q)
        response = tavily.search(query=q, max_results = 3, include_raw_content = True)
        for result in response['results']:
            context = "\n\n ".join(result['raw_content'])
    best_version = model.invoke([
        SystemMessage(content=HOTEL_EXPERT_PROMPT.format(hotels = context, city = state['Where_to'])),
        HumanMessage(content="Pick the best hotels based on the preference: " + state['Hotel_details']),
    ]).content
    return {"Hotel_expert": best_version}

def save_itinerary_to_md(city_name: str, itinerary: str):
            filename = f"{city_name.replace(' ', '_').lower()}_itinerary.md"
            with open(filename, 'w') as file:
                file.write(itinerary)


def Travel_Concierge_agent(state: AgentState):
    user_message = HumanMessage(
        content = f"""The above are my travel plans from {state['Where_from']} to {state['Where_to']} Provide me
        a Iternary."""
    )
    system_message = SystemMessage(content=TRAVEL_CONCIERGE_PROMPT.format(departure_date = state['Departure_date'],
    return_date = state['Return_date'],
    Local_expert = state['Local_expert'],
    Hotel_expert = state['Hotel_expert']))
    messages = [system_message, user_message]
    response = model.invoke(messages)
    save_itinerary_to_md(state['Where_to'], response.content)
    return {"FINAL_DRAFT": response.content}

builder = StateGraph(AgentState)
builder.add_node("local_guide", Local_expert_agent)
builder.add_node("hotel_expert", Hotel_expert_agent)
builder.add_node("travel_concierge", Travel_Concierge_agent)
builder.set_entry_point("local_guide")
builder.add_edge("local_guide", "hotel_expert")
builder.add_edge("hotel_expert", "travel_concierge")
builder.add_edge("travel_concierge", END)
graph = builder.compile()

def icon(emoji: str):
    """Shows an emoji as a Notion-style page icon."""
    st.write(
        f'<span style="font-size: 78px; line-height: 1">{emoji}</span>',
        unsafe_allow_html=True,
    )

# Set the page configuration
st.set_page_config(
    page_title="Travel Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="auto",
)

# Title and introduction
icon("Travel Planner")
st.subheader("Welcome to the Travel Planner! Provide your travel details in the sidebar, and we'll help you plan your trip.", divider="rainbow", anchor=False)

# Input form in sidebar
with st.sidebar:
    st.header("Trip Details")
    with st.form("travel_form"):
        where_from = st.text_input("Where are you traveling from? 🌍", "")
        where_to = st.text_input("Where are you traveling to? 🏖️", "")
        hotel_details = st.text_input("Hotel Preferences 🏨", "")
        departure_date = st.date_input("Departure Date 📅", value=None)
        return_date = st.date_input("Return Date 📅", value=None)
        submitted = st.form_submit_button("Plan My Trip")

    st.divider()

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
    else:
        with st.status("🤖 **Agents at work...**", state="running", expanded=True) as status:
            with st.container(height=500, border=False):
                for step in graph.stream({
                "Where_from": where_from,
                "Where_to": where_to,
                "Hotel_details": hotel_details,
                "Departure_date": departure_date,
                "Return_date": return_date,
            }):
                    st.write(step)
            status.update(label="✅ Trip Plan Ready!", state="complete", expanded=False)

        st.subheader("Here is your Trip Plan", anchor=False, divider="rainbow")
        st.markdown(step['travel_concierge']['FINAL_DRAFT'])