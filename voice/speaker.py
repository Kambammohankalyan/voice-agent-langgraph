import os
import asyncio
import edge_tts
import pygame

# CONFIG: Faster Rate & "Brian" (Jarvis-like)
VOICE = "en-IN-NeerjaNeural"
RATE = "+25%"  # <--- Speed boost

OUTPUT_FILE = "ai_response.mp3"

def speak(text):
    if not text: return
    
    async def _generate_audio():
        # Added 'rate' parameter for speed
        communicate = edge_tts.Communicate(text, VOICE, rate=RATE)
        await communicate.save(OUTPUT_FILE)

    try:
        # Generate Audio
        asyncio.run(_generate_audio())

        # Play Audio (Fast Load)
        pygame.mixer.init()
        pygame.mixer.music.load(OUTPUT_FILE)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        pygame.mixer.music.unload()
        try:
            os.remove(OUTPUT_FILE) # Clean up file immediately
        except:
            pass

    except Exception as e:
        print(f"❌ Audio Error: {e}")