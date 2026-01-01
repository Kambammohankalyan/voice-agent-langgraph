import whisper
import pyttsx3
import speech_recognition as sr
import time

# 1. Setup the "Mouth" (TTS)
# We use pyttsx3 because it is offline and FAST (<200ms)
engine = pyttsx3.init()
engine.setProperty('rate', 170) # Speed of speech

def speak(text):
    print(f"🤖 AI: {text}")
    engine.say(text)
    engine.runAndWait()

# 2. Setup the "Ears" (Whisper)
# We load the 'base' model. It is small (~140MB) and fast.
print("⏳ Loading Whisper Model... (This happens only once)")
model = whisper.load_model("base")
print("✅ Model Loaded!")

# CHANGE THIS to the Index number you found in Step 1
# Example: MIC_INDEX = 1
MIC_INDEX = 3  # <--- Try 0, then 1, then 2 if it doesn't work

def listen_and_transcribe():
    recognizer = sr.Recognizer()
    
    # FORCE SENSITIVITY: 
    # 300 is sensitive, 4000 is loud. 
    # If it still doesn't hear you, lower this to 150.
    recognizer.energy_threshold = 300  
    recognizer.dynamic_energy_threshold = False # Turn off auto-adjust
    
    # Explicitly use the correct microphone
    with sr.Microphone(device_index=MIC_INDEX) as source:
        print(f"🎤 Listening on Device {MIC_INDEX}... (Speak immediately!)")
        
        try:
            # timeout=None means it will wait forever until it hears sound
            # phrase_time_limit=5 means it cuts off 5 seconds AFTER it starts hearing sound
            audio = recognizer.listen(source, timeout=None, phrase_time_limit=5)
            
            print("⏳ Audio captured! Transcribing...")
            
            with open("temp.wav", "wb") as f:
                f.write(audio.get_wav_data())
            
            result = model.transcribe("temp.wav")
            text = result['text']
            
            if not text.strip():
                print("⚠️ Audio was empty.")
                return None
                
            print(f"You said: {text}")
            return text
            
        except Exception as e:
            print(f"Error: {e}")
            return None
# 3. The Main Loop
if __name__ == "__main__":
    speak("System Online.")
    
    while True:
        user_text = listen_and_transcribe()
        
        if user_text:
            if "exit" in user_text.lower():
                speak("Shutting down.")
                break
            
            # THE ECHO: Just repeat what I said
            speak(f"I heard you say: {user_text}")