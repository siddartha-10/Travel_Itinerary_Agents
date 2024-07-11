from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from langgraph.graph import StateGraph, END
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from tavily import TavilyClient
import os
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Azure OpenAI and Tavily clients
model = AzureChatOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_VERSION"),
    deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
)
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

MARKET_ANALYSIS_PROMPT = """You are an expert market analyst tasked to analyse the current market conditions and tasks.\
    using the Tavily API for search"""
STOCK_SCREENER_PROMPT = """You specialize in finding the best stocks by using the market analysis agent. \
"""
RISK_ASSESSOR_PROMPT = """Evaluate the risk associated with potential stock picks.\
You are adept at assessing risks, ensuring that investments align with the user's risk tolerance.\
"""
PERFORMANCE_PREDICTOR_PROMPT = """Your expertise lies in predicting stock performance using historical data and current trends. \
"""
REPORT_GENERATOR_PROMPT = """You are an expert in compiling all the findings into a clean and human understandable report. \
"""
from langchain_core.pydantic_v1 import BaseModel

class Queries(BaseModel):
    queries: List[str]

# Define input model
class InvestmentInput(BaseModel):
    risk: str
    investment_amount: float
    investment_time: str
    specific_sectors: List[str]

# Define agent state
class AgentState(BaseModel):
    market_analysis: str 
    stock_screener: str 
    risk_assessor: str 
    performance_predictor: str 
    report_generator: str 
    content: List[str] 

# Define agent nodes
def market_analysis_node(state: AgentState):
    content_human = f"Risk: {state.risk}, Investment amount: {state.investment_amount}, Investment time: {state.investment_time}, Specific sectors: {', '.join(state.specific_sectors)}"
    messages = [
        SystemMessage(content=MARKET_ANALYSIS_PROMPT),
        HumanMessage(content=content_human)
    ]
    response = model.invoke(messages)
    return AgentState(**{**state.dict(), "market_analysis": response.content})

def stock_screener_node(state: AgentState):
    content_human = f"Risk: {state.risk}, Investment amount: {state.investment_amount}, Investment time: {state.investment_time}, Specific sectors: {', '.join(state.specific_sectors)}"
    queries = model.with_structured_output(Queries).invoke([
        SystemMessage(content=STOCK_SCREENER_PROMPT),
        HumanMessage(content=f"{content_human}\n\n{state.market_analysis}")
    ])
    content = state.content or []
    for q in queries.queries:
        response = tavily_client.search(q, max_results=2)
        for r in response['results']:
            content.append(r['content'])
    return AgentState(**{**state.dict(), "content": content, "stock_screener": "\n".join(content)})

def risk_assessor_node(state: AgentState):
    content_human = f"Risk: {state.risk}, Investment amount: {state.investment_amount}, Investment time: {state.investment_time}, Specific sectors: {', '.join(state.specific_sectors)}"
    user_message = HumanMessage(content=f"{content_human}\n\nHere are the list of stocks:\n\n{state.stock_screener}")
    messages = [
        SystemMessage(content=RISK_ASSESSOR_PROMPT),
        user_message
    ]
    response = model.invoke(messages)
    return AgentState(**{**state.dict(), "risk_assessor": response.content})

def performance_node(state: AgentState):
    queries = model.with_structured_output(Queries).invoke([
        SystemMessage(content=PERFORMANCE_PREDICTOR_PROMPT),
        HumanMessage(content=f"\n\nHere are the stock picks and their risk assessments:\n{state.risk_assessor}\n{state.stock_screener}")
    ])
    content = state.content or []
    for q in queries.queries:
        response = tavily_client.search(q, max_results=2)
        for r in response['results']:
            content.append(r['content'])
    return AgentState(**{**state.dict(), "performance_predictor": "\n".join(content)})

def report_node(state: AgentState):
    content_human = f"Risk: {state.risk}, Investment amount: {state.investment_amount}, Investment time: {state.investment_time}, Specific sectors: {', '.join(state.specific_sectors)}"
    content = "\n\n".join(state.content or [])
    user_message = HumanMessage(content=f"{content_human}\n\nHere is the performance of the stocks:\n\n{state.performance_predictor}")
    messages = [
        SystemMessage(content=REPORT_GENERATOR_PROMPT.format(content=content)),
        user_message
    ]
    response = model.invoke(messages)
    return AgentState(**{**state.dict(), "report_generator": response.content})

# Build the graph
def build_graph():
    builder = StateGraph(AgentState)
    builder.add_node("market_analyst", market_analysis_node)
    builder.add_node("stocks_screener", stock_screener_node)
    builder.add_node("risk_assessment", risk_assessor_node)
    builder.add_node("performance_analysis", performance_node)
    builder.add_node("report_generations", report_node)
    builder.set_entry_point("market_analyst")
    builder.add_edge("market_analyst", "stocks_screener")
    builder.add_edge("stocks_screener", "risk_assessment")
    builder.add_edge("risk_assessment", "performance_analysis")
    builder.add_edge("performance_analysis", "report_generations")
    builder.add_edge("report_generations", END)
    return builder.compile()

graph = build_graph()

@app.post("/generate-investment-advice")
async def generate_investment_advice(input_data: InvestmentInput):
    initial_state = AgentState(**input_data.dict())
    for s in graph.stream(initial_state):
        if s.report_generator:
            return {"report": s.report_generator}
    return {"error": "Failed to generate investment advice"}