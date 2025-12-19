import speech_recognition as sr
import pyaudio
import sys

def test_mic(index, name):
    print(f"\n--- Testing Mic [{index}] {name} ---")
    r = sr.Recognizer()
    try:
        with sr.Microphone(device_index=index) as source:
            print("Adjusting noise...")
            r.adjust_for_ambient_noise(source, duration=0.5)
            print(f"Energy cycle: {r.energy_threshold}")
            if r.energy_threshold < 50:
                 print("WARNING: Low energy threshold (Mic might be muted or silent)")
            
            print("Say something (3s)...")
            try:
                audio = r.listen(source, timeout=3, phrase_time_limit=3)
                print("Audio captured!")
                try:
                    text = r.recognize_google(audio)
                    print(f"SUCCESS: Recognized: '{text}'")
                    return True
                except sr.UnknownValueError:
                    print("Recognized: <Unintelligible Audio> (But mic passed)")
                    return True
            except sr.WaitTimeoutError:
                print("Timeout: No speech detected.")
    except Exception as e:
        print(f"Error: {e}")
    return False

mics = sr.Microphone.list_microphone_names()
candidates = [i for i, m in enumerate(mics) if "Microphone" in m or "Input" in m]

print(f"Found candidates: {candidates}")

for i in candidates:
    if test_mic(i, mics[i]):
        print(f"\n✅ FOUND WORKING MIC: Index {i}")
        break
else:
    print("\n❌ NO WORKING MIC FOUND")
