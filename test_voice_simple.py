"""
Simple test to check if voice recognition is working
"""
import speech_recognition as sr

print("Testing voice recognition...")
print("=" * 60)

# Create recognizer
recognizer = sr.Recognizer()

# List microphones
try:
    mics = sr.Microphone.list_microphone_names()
    print(f"\nFound {len(mics)} microphones:")
    for i, mic in enumerate(mics):
        print(f"  [{i}] {mic}")
except Exception as e:
    print(f"Error listing microphones: {e}")
    print("\nThis might indicate PyAudio is not properly installed.")
    print("Try: pip install pyaudio")
    exit(1)

print("\n" + "=" * 60)
print("\nTesting microphone access...")

try:
    # Try to access default microphone
    with sr.Microphone() as source:
        print("✓ Microphone access successful!")
        print("\nAdjusting for ambient noise... (please wait)")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("✓ Ambient noise adjustment complete")
        
        print("\n" + "=" * 60)
        print("Please speak something now...")
        print("=" * 60)
        
        audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
        print("✓ Audio captured!")
        
        print("\nRecognizing speech...")
        try:
            text = recognizer.recognize_google(audio)
            print(f"✓ Recognized: '{text}'")
        except sr.UnknownValueError:
            print("✗ Could not understand audio")
        except sr.RequestError as e:
            print(f"✗ Google API error: {e}")
            
except OSError as e:
    print(f"✗ Microphone access error: {e}")
    print("\nPossible issues:")
    print("  1. PyAudio not properly installed")
    print("  2. No microphone connected")
    print("  3. Microphone permissions not granted")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Test complete!")
