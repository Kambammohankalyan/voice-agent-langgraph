import os
import speech_recognition as sr
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def listen(mic_index=1): # <--- KEPT YOUR INDEX 1
    r = sr.Recognizer()
    
    # 1. NOISE FILTERING
    # Higher = Less Sensitive (300 is sensitive, 500-1000 is stricter)
    r.energy_threshold = 500  
    r.dynamic_energy_threshold = False 
    r.pause_threshold = 0.6
    
    with sr.Microphone(device_index=mic_index) as source:
        # Optional: Adjust for noise once at startup (can slow down first loop)
        # r.adjust_for_ambient_noise(source, duration=0.5)
        
        try:
            # Wait 1s for speech. If silence, stops waiting.
            audio = r.listen(source, timeout=1.0, phrase_time_limit=5)
            
            with open("temp.wav", "wb") as f: f.write(audio.get_wav_data())
            
            with open("temp.wav", "rb") as file:
                text = client.audio.transcriptions.create(
                    file=("temp.wav", file.read()),
                    model="whisper-large-v3-turbo",
                    prompt="Mohankalyan, M.Tech, NIT Raipur. English.",
                    language="en",
                    response_format="text"
                ).strip()
            
            # --- 2. THE TRASH FILTER ---
            # If the text matches ANY of these, ignore it.
            ghost_phrases = [
                "Thank you.", "Thank you", "You", "MBC", "Subtitles", 
                "Amara.org", "by", "The", "Copyright", "Copyright 2025"
            ]
            
            # Reject if in ghost list OR too short (less than 3 chars)
            if text in ghost_phrases or len(text) < 4: 
                return None
                
            return text
            
        except sr.WaitTimeoutError:
            return None # Silence is normal
        except Exception:
            return None