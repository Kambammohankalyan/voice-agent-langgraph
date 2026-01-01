import sys
import traceback

print("⏳ Initializing Modules...")

try:
    from langchain_core.messages import HumanMessage
    from voice import listener, speaker
    from backend.core import app
    import os
    print("✅ Modules Loaded.")
except Exception as e:
    print(f"❌ CRITICAL IMPORT ERROR: {e}")
    traceback.print_exc()
    sys.exit(1)

# CONFIGURATION
# ⚠️ UPDATE THIS NUMBER based on check_mics.py
MIC_INDEX = 1  

def main():
    print("🚀 Starting Main Loop...")
    
    # Test Speaker first to ensure audio works
    try:
        speaker.speak("System Diagnostics Online.")
    except Exception as e:
        print(f"⚠️ Speaker Error: {e}")

    # Conversation State
    config = {"configurable": {"thread_id": "Session-Debug-1"}}
    
    while True:
        try:
            # 1. Listen
            user_text = listener.listen(mic_index=MIC_INDEX)
            
            if user_text:
                print(f"👤 You: {user_text}")
                
                if "exit" in user_text.lower():
                    speaker.speak("Shutting down.")
                    break
                
                # 2. Think (LangGraph)
                print("🧠 Thinking...")
                result = app.invoke(
                    {"messages": [HumanMessage(content=user_text)]}, 
                    config=config
                )
                
                ai_response = result['messages'][-1].content
                
                # 3. Speak
                speaker.speak(ai_response)
                
        except OSError as e:
            print(f"\n❌ MICROPHONE ERROR: Could not access Device Index {MIC_INDEX}.")
            print(f"Error Details: {e}")
            print("👉 Run 'python check_mics.py' to find the correct index.")
            break
            
        except Exception as e:
            print(f"\n❌ UNEXPECTED ERROR: {e}")
            traceback.print_exc()
            break

if __name__ == "__main__":
    main()