import os
import time
import whisper
import pyttsx3
import speech_recognition as sr
from dotenv import load_dotenv
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver  # <--- NEW IMPORT
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# --- 1. SETUP ---
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MIC_INDEX = 3

# Setup Hardware
engine = pyttsx3.init()
engine.setProperty('rate', 160)
whisper_model = whisper.load_model("small") 
print("✅ Systems Online. Persistent Memory Active.")

def speak(text):
    print(f"🤖 AI: {text}")
    engine.say(text)
    engine.runAndWait()

# --- 2. THE BRAIN (WITH PERSISTENCE) ---

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

llm = ChatGroq(groq_api_key=GROQ_API_KEY, model_name="llama-3.1-8b-instant")

def chatbot_node(state: AgentState):
    messages = state['messages']
    
    # SYSTEM PROMPT: Strictly enforcing memory
    system_prompt = SystemMessage(content="""
    You are Jarvis. 
    1. You MUST remember the user's name and details from previous messages.
    2. If the user asks 'What is my name?', look at the conversation history.
    3. Be concise.
    """)
    
    response = llm.invoke([system_prompt] + messages)
    return {"messages": [response]}

# Build Graph WITH CHECKPOINTER
memory = MemorySaver()  # <--- The "Hard Drive" that fixes Amnesia
workflow = StateGraph(AgentState)
workflow.add_node("agent", chatbot_node)
workflow.set_entry_point("agent")
workflow.add_edge("agent", END)

# Compile with the checkpointer
app = workflow.compile(checkpointer=memory)

# --- 3. THE EARS ---
def listen_and_transcribe():
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 280
    recognizer.dynamic_energy_threshold = False
    recognizer.pause_threshold = 1.0 
    
    with sr.Microphone(device_index=MIC_INDEX) as source:
        print(f"\n🎤 Listening...")
        try:
            audio = recognizer.listen(source, timeout=None, phrase_time_limit=8)
            print("⚡ Transcribing...")
            with open("temp.wav", "wb") as f: f.write(audio.get_wav_data())
            
            # Context Injection to fix "NIT Raipur"
            context = "Kambam Mohankalyan, NIT Raipur, National Institute of Technology, AI."
            
            result = whisper_model.transcribe("temp.wav", language="en", initial_prompt=context, fp16=False)
            text = result['text'].strip()
            
            if not text: return None
            print(f"👤 You: {text}")
            return text
        except: return None

# --- 4. MAIN LOOP ---
if __name__ == "__main__":
    speak("Jarvis initialized. Memory ready.")
    
    # We use a Thread ID to simulate a continuous session
    config = {"configurable": {"thread_id": "Session-1"}}
    
    while True:
        user_text = listen_and_transcribe()
        
        if user_text:
            if "exit" in user_text.lower(): break
            
            print("🧠 Thinking...")
            
            # Pass the CONFIG so LangGraph knows it's the SAME conversation
            result = app.invoke(
                {"messages": [HumanMessage(content=user_text)]}, 
                config=config 
            )
            
            ai_response = result['messages'][-1].content
            speak(ai_response)