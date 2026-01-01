import os
from datetime import datetime
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, AIMessage
from langchain_community.tools.tavily_search import TavilySearchResults
from dotenv import load_dotenv
from backend import rag_engine

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

llm = ChatGroq(groq_api_key=GROQ_API_KEY, model_name="llama-3.1-8b-instant")

# --- TOOLS ---
def save_memory(text):
    # FILTER: Reject hallucinated placeholders or short junk
    if "<fact>" in text or "command" in text.lower() or len(text) < 10:
        return "Info unclear, ignored."
        
    print(f"💾 SAVING: {text}")
    with open("data/knowledge_base.txt", "a") as f:
        f.write(f"\n{text}")
    rag_engine.ingest_text(text)
    return "Saved."  # <--- Brief response

def search_memory(query):
    print(f"🧠 MEMORY: {query}")
    return rag_engine.retrieve(query)

def search_web(query):
    print(f"🔍 GOOGLE: {query}")
    try:
        tavily = TavilySearchResults(max_results=1) # Faster (1 result only)
        results = tavily.invoke(query)
        return results[0]['content'] # Return just the text
    except:
        return "No results."

def get_system_time():
    return datetime.now().strftime("%I:%M %p")

# --- BRAIN ---
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

def agent_node(state: AgentState):
    messages = state['messages']
    
    # SYSTEM PROMPT: Brief & Strict
    system_prompt = SystemMessage(content="""
    You are JARVIS. Be FAST and CONCISE.
    
    COMMANDS (Start response with):
    1. "CMD: SAVE | <fact>" (Only for explicit facts like "I live in X")
    2. "CMD: SEARCH | <query>" (For "Who am I?", "Where do I live?")
    3. "CMD: GOOGLE | <query>" (For Weather, Stocks, Facts)
    4. "CMD: TIME" (For time)
    
    RULES:
    - Do NOT save random chat. Only save FACTS.
    - If user says "Omnodx" or gibberish, just ignore or ask to repeat.
    - Keep normal chat responses under 1 sentence.
    """)
    
    response = llm.invoke([system_prompt] + messages)
    content = response.content.strip()
    
    # HANDLERS
    if "CMD: SAVE |" in content:
        raw_fact = content.split("CMD: SAVE |")[1].strip()
        fact = raw_fact.strip('"').split("\n")[0]
        result = save_memory(fact)
        # Check if save was ignored
        if "ignored" in result:
             return {"messages": [AIMessage(content="I didn't catch that fact clearly.")]}
        return {"messages": [AIMessage(content="Got it.")]} # <--- Shortest reply
        
    elif "CMD: SEARCH |" in content:
        query = content.split("|", 1)[1].strip().split('"')[0]
        context = search_memory(query)
        final = llm.invoke([SystemMessage(content=f"Info: {context}. User Question: {messages[-1].content}")] + messages)
        return {"messages": [final]}
        
    elif "CMD: GOOGLE |" in content:
        query = content.split("|", 1)[1].strip().split('"')[0]
        data = search_web(query)
        final = llm.invoke([SystemMessage(content=f"Web: {data}. User Question: {messages[-1].content}")] + messages)
        return {"messages": [final]}
        
    elif "CMD: TIME" in content:
        return {"messages": [AIMessage(content=f"It's {get_system_time()}.")]}
        
    return {"messages": [response]}

workflow = StateGraph(AgentState)
workflow.add_node("agent", agent_node)
workflow.set_entry_point("agent")
workflow.add_edge("agent", END)

app = workflow.compile(checkpointer=MemorySaver())