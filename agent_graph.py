import os
from dotenv import load_dotenv
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

# 1. Load Secrets
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# 2. Define the "Memory State"
class AgentState(TypedDict):
    messages: list  # This list stores the entire conversation history!

# 3. Setup the Brain (Groq with LangChain)
llm = ChatGroq(
    groq_api_key=GROQ_API_KEY, 
    model_name="llama-3.1-8b-instant",
    temperature=0.6
)

# 4. Define the Node (The "Thinking" Step)
def call_model(state: AgentState):
    messages = state['messages']
    
    # Add a System Prompt if it's the start
    if len(messages) == 1:
        system_prompt = SystemMessage(content="You are Jarvis. You MUST remember the user's name and details. Be concise.")
        messages = [system_prompt] + messages
        
    response = llm.invoke(messages)
    return {"messages": [response]}

# 5. Build the Graph
workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.set_entry_point("agent")
workflow.add_edge("agent", END)

# 6. Compile the Application
app = workflow.compile()

# --- TEST FUNCTION ---
if __name__ == "__main__":
    print("🤖 Graph Initialized. Testing Memory...")
    
    # Message 1: Tell it your name
    print("👤 You: My name is Mohankalyan.")
    input_1 = {"messages": [HumanMessage(content="My name is Mohankalyan.")]}
    output_1 = app.invoke(input_1)
    print(f"🤖 AI: {output_1['messages'][-1].content}")
    
    # Message 2: Ask it your name (To test Memory)
    # IMPORTANT: We pass the FULL history back into the next step
    print("\n👤 You: What is my name?")
    input_2 = {"messages": output_1['messages'] + [HumanMessage(content="What is my name?")]}
    output_2 = app.invoke(input_2)
    print(f"🤖 AI: {output_2['messages'][-1].content}")