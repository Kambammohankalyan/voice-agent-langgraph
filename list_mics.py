import speech_recognition as sr

print("🔍 Scanning for microphones...")
mics = sr.Microphone.list_microphone_names()

for i, mic_name in enumerate(mics):
    print(f"Index {i}: {mic_name}")

print("\n👉 Look for your headset or main microphone in the list above.")
print("👉 Note the INDEX number (e.g., 1, 2, or 0).")