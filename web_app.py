import streamlit as st
import os
import asyncio
import edge_tts
import base64
import time
from pypdf import PdfReader
from langchain_core.messages import HumanMessage, AIMessage
from backend.core import app
from backend import rag_engine
from groq import Groq

# --- CONFIGURATION ---
st.set_page_config(
    page_title="JARVIS | Document Core",
    page_icon="🤖",
    layout="wide"
)

# Groq Client for Transcription
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# --- STYLES ---
st.markdown("""
    <style>
    .stApp {background-color: #0e1117; color: #ffffff;}
    .stChatMessage {background-color: #262730; border-radius: 10px; border: 1px solid #444;}
    .big-font {font-size:20px !important; font-weight: bold; color: #00ff00;}
    </style>
""", unsafe_allow_html=True)

# --- AUDIO FUNCTIONS ---
async def generate_audio_file(text):
    """Generates MP3 audio"""
    voice = "en-US-BrianNeural"
    output_file = "reply.mp3"
    # Clean text for better speech
    text = text.replace("*", "").replace("#", "").replace("-", " ")
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)
    return output_file

def autoplay_audio(file_path):
    """Plays audio automatically"""
    with open(file_path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    md = f"""
        <audio controls autoplay style="width: 100%;">
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
    """
    st.markdown(md, unsafe_allow_html=True)

def transcribe_voice(audio_bytes):
    """Converts Voice to Text"""
    if not audio_bytes: return None
    try:
        audio_bytes.name = "audio.wav"
        return client.audio.transcriptions.create(
            file=audio_bytes,
            model="whisper-large-v3-turbo",
            response_format="text",
            language="en"
        ).strip()
    except Exception as e:
        st.error(f"Transcription Error: {e}")
        return None

# --- SIDEBAR: FILE HANDLING ---
with st.sidebar:
    st.title("📂 Knowledge Base")
    
    # 1. Clear Memory Button (CRITICAL FIX)
    if st.button("🗑️ Reset Brain (Clear Old Data)"):
        # This is a hacky way to simulate clearing context in this simple setup
        # ideally you would delete from Pinecone, but for now we just clear the session source
        st.session_state.current_source = None
        st.session_state.messages = []
        st.success("Memory Wiped.")
        time.sleep(1)
        st.rerun()

    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
    
    if uploaded_file:
        # Check if it's a new file
        if "current_source" not in st.session_state or st.session_state.current_source != uploaded_file.name:
            with st.status("⚙️ Ingesting Document...", expanded=True) as status:
                st.write("📖 Reading Text...")
                pdf = PdfReader(uploaded_file)
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
                
                st.write("🧠 Memorizing...")
                # Chunking
                chunk_size = 1000
                chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
                
                # We tag the data with the filename so we only search THIS file later
                for chunk in chunks:
                    # Ingest with a specific tag
                    rag_engine.ingest_text(f"SOURCE_FILE: {uploaded_file.name} | CONTENT: {chunk}")
                
                st.session_state.current_source = uploaded_file.name
                status.update(label="✅ Ready", state="complete", expanded=False)

# --- MAIN CHAT ---
st.title("🤖 JARVIS PDF Chat")

# Session History
if "messages" not in st.session_state:
    st.session_state.messages = [AIMessage(content="System Online. Upload a PDF and ask me about it.")]

# Render Chat
for msg in st.session_state.messages:
    if isinstance(msg, HumanMessage):
        with st.chat_message("user", avatar="👤"):
            st.write(msg.content)
    elif isinstance(msg, AIMessage):
        with st.chat_message("assistant", avatar="🤖"):
            st.write(msg.content)

# INPUTS
voice_input = st.audio_input("🎤 Voice Command")
text_input = st.chat_input("💬 Type Command")

user_text = None

# Process Input
if voice_input:
    user_text = transcribe_voice(voice_input)
elif text_input:
    user_text = text_input

if user_text:
    # 1. Show User Text (So you see if it heard "Project" or "Object")
    st.session_state.messages.append(HumanMessage(content=user_text))
    with st.chat_message("user", avatar="👤"):
        st.write(user_text)

    # 2. AI Processing
    with st.chat_message("assistant", avatar="🤖"):
        status = st.empty()
        status.markdown("🔵 *Searching PDF...*")
        
        # --- FIX: Strict Search ---
        # We append the filename to the search query to prioritize the current PDF
        search_query = f"{user_text}"
        if "current_source" in st.session_state:
            # We add context to the retrieval query
            search_query += f" {st.session_state.current_source}"
            
        context_data = rag_engine.retrieve(search_query)
        
        # --- FIX: Strict Prompt ---
        # Explicitly tell it to IGNORE outside knowledge if it conflicts
        strict_prompt = f"""
        You are an assistant analyzing a specific document.
        
        DOCUMENT CONTEXT:
        {context_data}
        
        USER QUESTION:
        {user_text}
        
        INSTRUCTIONS:
        1. Answer ONLY based on the Document Context above.
        2. If the context mentions 'Projects' (like Voice Agent, Pricing Engine), talk about those.
        3. Do NOT talk about 'objects' or 'feature interactions' unless they are in the text above.
        4. Be concise and professional.
        """
        
        status.markdown("🟣 *Thinking...*")
        
        # Invoke Brain
        config = {"configurable": {"thread_id": "Web-Session-Strict"}}
        result = app.invoke(
            {"messages": [HumanMessage(content=strict_prompt)]}, 
            config=config
        )
        ai_response = result['messages'][-1].content
        
        # Show and Speak
        status.write(ai_response)
        st.session_state.messages.append(AIMessage(content=ai_response))
        
        asyncio.run(generate_audio_file(ai_response))
        autoplay_audio("reply.mp3")