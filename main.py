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
# model = ChatOpenAI(temperature=0.3, model='gpt-4-turbo')

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
def Local_expert_agent(state: AgentState):
    queries = model.with_structured_output(Queries).invoke([
        SystemMessage(content=LOCAL_EXPERT_QUERIES_PROMPT),
        HumanMessage(content = state['Where_to']),
    ])
    context = ""
    for q in queries.queries:
        response = tavily.search(query=q, max_results = 5, include_raw_content = True, include_domains = ["expedia.com"])
        for result in response['results']:
            context = "\n\n ".join(result['raw_content'])
    best_version = model.invoke([
        SystemMessage(content=LOCAL_EXPERT_PROMPT.format(city = state['Where_to'])),
        HumanMessage(content = context),
    ]).content
    return {"Local_expert": best_version}
HOTEL_EXPERT_QUERIES_PROMPT = """ 
Generate single query to find the best hotels that fits the user preferences {user_preferences} in the {city} only. \
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
def Hotel_expert_agent(state: AgentState):
    queries = model.with_structured_output(Queries).invoke([
        SystemMessage(content=HOTEL_EXPERT_QUERIES_PROMPT.format(city = state['Where_to'],
        user_preferences = state['Hotel_details'])),
        HumanMessage(content = "\n\n" + "Here is my preferences to finding a hotel "+ state['Hotel_details']),
    ])
    context = ""
    for q in queries.queries:
        response = tavily.search(query=q, max_results = 5, include_raw_content = True, include_domains = ["expedia.com", "booking.com"])
        for result in response['results']:
            context = "\n\n ".join(result['raw_content'])
    best_version = model.invoke([
        SystemMessage(content=HOTEL_EXPERT_PROMPT.format(hotels = context, city = state['Where_to'])),
        HumanMessage(content="Pick the best hotels based on the preference: " + state['Hotel_details']),
    ]).content
    return {"Hotel_expert": best_version}
TRAVEL_EXPERT_PROMPT_QUERY = """ You are great at finding the best and cheapest travel \
Accommodations, based on the travel date {Departure_date} and return date {Return_date} \
from {Where_from} to {Where_to}. 

your goal is to find travel and not accommodation

Generate 2 queries at max based on the trip details and also you goals is to find the best and cheapest prices.\
Stick with return trip mainly rather than one way ticket.
"""
TRAVEL_EXPERT_PROMPT = """ 
Organise these Travel details In provided order below use you creativity to order the travel plans but do not change of the information
provided below by the user. {User_preference}


A list of the top 3-4 options.
For each option, provide:
Type Flight or Bus etc
To and from
URL_LINK:
Any additional relevant details (baggage included, flight change policies, etc.)
"""
def Travel_expert_agent(state: AgentState):
    queries = model.with_structured_output(Queries).invoke([
        SystemMessage(content=TRAVEL_EXPERT_PROMPT_QUERY.format(
        Departure_date = state['Departure_date'], Return_date = state['Return_date'],
        Where_from = state['Where_from'], Where_to = state['Where_to'])),
        HumanMessage(content = "\n\n" + "Here is my travel preferences "+ state['Travel_preference']),
    ])
    url = "https://api-ares.traversaal.ai/live/predict"
    for q in queries.queries:
        payload = { "query": [q] }
        headers = {
            "x-api-key": os.environ.get("TRAVERSAL_AI_API_CURRENT"),
            "content-type": "application/json"
        }
        response = requests.post(url, json=payload, headers=headers)
        # print(response)
        string_data = response.content.decode('utf-8')

        # Parse JSON string to a Python dictionary
        json_data = json.loads(string_data)
        context = "\n\n ".join(json_data['data']['response_text'])
        context = "These are the URL for the flight details ".join(json_data['data']['web_url'])
    best_version = model.invoke([
        SystemMessage(content=TRAVEL_EXPERT_PROMPT.format(User_preference = state['Travel_preference'])),
        HumanMessage(content = context),
    ]).content
    return {"Travel_expert": best_version}

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
Here are some of the travel plans {Travel_expert}

example:-

Day 1: Arrival and Exploring the City
Weather Forecast: High of 88°F, Low of 78°F. Partly cloudy with a chance of afternoon showers.

Morning:
Arrival from India to Miami via your selected flight option. (Travel Plan Option 1)
Check-in at the Hampton Inn & Suites by Hilton Miami Brickell Downtown.
Afternoon:

Lunch at Versailles Restaurant in Little Havana, known for its authentic Cuban cuisine.
Explore Little Havana, the heart of Miami's Cuban community, and immerse yourself in the vibrant culture. Visit the local cigar shops and art galleries.
Evening:

Enjoy a stroll around the Art Deco Historic District with its historic architecture from the 1920s and 1930s.
Dinner at Joe's Stone Crab, a famous seafood restaurant in South Beach.
Experience Miami's nightlife in South Beach. Visit The Clevelander Bar for a fun and vibrant experience.

What to Pack: Swimwear, sunscreen, light clothing, comfortable walking shoes, a light rain jacket (just in case of showers), and a camera.


The example of Day 1 should continue for rest of the days and what to pack depends upon that days sechdule and where
we are going.

Hotels:-
1_ .....
2) ....

Transportation:-
2) .....
3) .....

What to pack:-
1) ......
2) .....

"""
def Travel_Concierge_agent(state: AgentState):
    user_message = HumanMessage(
        content = f"""The above are my travel plans from {state['Where_from']} to {state['Where_to']} Provide me
        a Iternary."""
    )
    system_message = SystemMessage(content=TRAVEL_CONCIERGE_PROMPT.format(departure_date = state['Departure_date'],
    return_date = state['Return_date'],
    Local_expert = state['Local_expert'],
    Hotel_expert = state['Hotel_expert'], Travel_expert = state['Travel_expert']))
    messages = [system_message, user_message]
    response = model.invoke(messages)
    return {"FINAL_DRAFT": response.content}

builder = StateGraph(AgentState)
builder.add_node("local_guide", Local_expert_agent)
builder.add_node("hotel_expert", Hotel_expert_agent)
builder.add_node("travel_expert", Travel_expert_agent)
builder.add_node("travel_concierge", Travel_Concierge_agent)
builder.set_entry_point("local_guide")
builder.add_edge("local_guide", "hotel_expert")
builder.add_edge("hotel_expert", "travel_expert")
builder.add_edge("travel_expert", "travel_concierge")
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
st.subheader("Let AI agents plan your next vacation!", divider="rainbow", anchor=False)

# Input form in sidebar
with st.sidebar:
    st.header("Trip Details")
    with st.form("travel_form"):
        where_from = st.text_input("Where are you traveling from? 🌍", "")
        where_to = st.text_input("Where are you traveling to? 🏖️", "")
        hotel_details = st.text_input("Hotel Preferences 🏨", "")
        departure_date = st.date_input("Departure Date 📅", value=None)
        return_date = st.date_input("Return Date 📅", value=None)
        travel_preference = st.selectbox("Travel Preference ✈️", ["", "Flight", "Train", "Car", "Bus"])

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
    elif not travel_preference or travel_preference == "":
        st.error("Please select a 'Travel Preference'!")
    else:
        with st.status("🤖 **Agents at work...**", state="running", expanded=True) as status:
            with st.container(height=500, border=False):
                for s in graph.stream({
                "Where_from": where_from,
                "Where_to" : where_to,
                "Hotel_details": hotel_details,
                "Departure_date": departure_date,
                "Return_date": return_date,
                "Travel_preference": travel_preference,
                }): 
                    st.write(s)
            status.update(label="✅ Trip Plan Ready!", state="complete", expanded=False)

        st.subheader("Here is your Trip Plan", anchor=False, divider="rainbow")
        st.markdown(s['travel_concierge']['FINAL_DRAFT'])

if __name__ == "__main__":
    st.markdown("Welcome to the Travel Planner! Provide your travel details in the sidebar, and we'll help you plan your trip.")