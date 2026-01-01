import whisper
import pyttsx3
import speech_recognition as sr
import time
import os
from groq import Groq
from dotenv import load_dotenv  # <--- NEW IMPORT

# 1. Load Environment Variables
load_dotenv()

# 2. Get the Key securely
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    print("❌ ERROR: GROQ_API_KEY not found in .env file!")
    exit(1)

# --- CONFIGURATION ---
MIC_INDEX = 3  # Based on your previous success
client = Groq(api_key=GROQ_API_KEY)

engine = pyttsx3.init()
engine.setProperty('rate', 160)

def speak(text):
    print(f"🤖 AI: {text}")
    engine.say(text)
    engine.runAndWait()

print("⏳ Loading Whisper Model...")
model = whisper.load_model("base")
print("✅ Systems Online. Metrics Active.")

def listen_and_transcribe():
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = False
    
    with sr.Microphone(device_index=MIC_INDEX) as source:
        print(f"\n🎤 Listening...")
        try:
            audio = recognizer.listen(source, timeout=None, phrase_time_limit=5)
            
            # METRIC 1: Transcription Time
            start_time = time.time()
            print("⚡ Transcribing...")
            
            with open("temp.wav", "wb") as f:
                f.write(audio.get_wav_data())
            
            result = model.transcribe("temp.wav", language="en")
            text = result['text'].strip()
            
            end_time = time.time()
            transcription_time = end_time - start_time
            
            if not text: return None, 0
            
            print(f"👤 You: {text}")
            print(f"⏱️ Whisper Latency: {transcription_time:.2f}s")
            return text, transcription_time
            
        except Exception as e:
            return None, 0

def query_llm(user_text):
    # METRIC 2: Groq Inference Time
    start_time = time.time()
    print("🧠 Thinking...")
    
    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are Jarvis. Be ultra-fast and concise. Answer in 1 sentence."},
            {"role": "user", "content": user_text}
        ],
        temperature=0.7,
        max_tokens=50,
        stream=False
    )
    
    end_time = time.time()
    inference_time = end_time - start_time
    
    response = completion.choices[0].message.content
    print(f"⏱️ Groq Latency: {inference_time:.2f}s") 
    return response

# --- MAIN LOOP ---
if __name__ == "__main__":
    speak("Secure Systems Online.")
    
    while True:
        user_input, trans_time = listen_and_transcribe()
        
        if user_input:
            if "exit" in user_input.lower():
                speak("Shutting down.")
                break
            
            response = query_llm(user_input)
            speak(response)