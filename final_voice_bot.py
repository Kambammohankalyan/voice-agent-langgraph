import os
import time
import pyttsx3
import speech_recognition as sr
from dotenv import load_dotenv
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from groq import Groq 

# --- 1. SETUP ---
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MIC_INDEX = 3 # Ensure this is your working Mic Index

if not GROQ_API_KEY:
    print("❌ ERROR: GROQ_API_KEY not found!")
    exit(1)

# Initialize Clients
groq_client = Groq(api_key=GROQ_API_KEY) 
llm = ChatGroq(groq_api_key=GROQ_API_KEY, model_name="llama-3.1-8b-instant")

# Setup TTS (Mouth)
engine = pyttsx3.init()
engine.setProperty('rate', 175) # Fast, energetic speed
engine.setProperty('volume', 1.0)

print("✅ Connected to Groq Cloud. Turbo Mode Active.")

def speak(text):
    print(f"🤖 AI: {text}")
    engine.say(text)
    engine.runAndWait()

# --- 2. THE BRAIN (LANGGRAPH) ---
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

def chatbot_node(state: AgentState):
    messages = state['messages']
    
    # SYSTEM PROMPT: Speed & Memory
    system_prompt = SystemMessage(content="""
    You are Jarvis. 
    1. Answer in 1 short sentence (max 15 words).
    2. Only give long details if explicitly asked "in detail".
    3. Remember the user's name: Mohankalyan.
    """)
    
    response = llm.invoke([system_prompt] + messages)
    return {"messages": [response]}

memory = MemorySaver()
workflow = StateGraph(AgentState)
workflow.add_node("agent", chatbot_node)
workflow.set_entry_point("agent")
workflow.add_edge("agent", END)
app = workflow.compile(checkpointer=memory)

# --- 3. THE EARS (GROQ TURBO WHISPER) ---
def listen_and_transcribe():
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = False
    recognizer.pause_threshold = 0.6  # Fast snap
    
    with sr.Microphone(device_index=MIC_INDEX) as source:
        print(f"\n🎤 Listening...")
        try:
            audio = recognizer.listen(source, timeout=None, phrase_time_limit=5)
            
            # Write to disk
            with open("temp.wav", "wb") as f:
                f.write(audio.get_wav_data())
            
            start_time = time.time()
            print("⚡ Uploading to Groq...")
            
            # UPDATED MODEL NAME HERE
            with open("temp.wav", "rb") as file:
                transcription = groq_client.audio.transcriptions.create(
                    file=("temp.wav", file.read()),
                    model="whisper-large-v3-turbo", # <--- THE FIX
                    response_format="text",
                    prompt="Mohankalyan, NIT Raipur, AI context" # Context Hint
                )
            
            text = transcription.strip()
            trans_time = time.time() - start_time
            
            if not text: return None
            
            print(f"👤 You: {text}")
            print(f"⏱️ Transcription Latency: {trans_time:.2f}s")
            return text
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return None

# --- 4. MAIN LOOP ---
if __name__ == "__main__":
    speak("Turbo Systems Online.")
    config = {"configurable": {"thread_id": "TurboSession-1"}}
    
    while True:
        user_text = listen_and_transcribe()
        
        if user_text:
            if "exit" in user_text.lower(): break
            
            start_think = time.time()
            
            result = app.invoke(
                {"messages": [HumanMessage(content=user_text)]}, 
                config=config 
            )
            
            groq_time = time.time() - start_think
            print(f"⏱️ Inference Latency: {groq_time:.2f}s")
            
            ai_response = result['messages'][-1].content
            speak(ai_response)