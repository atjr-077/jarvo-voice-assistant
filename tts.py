import pyttsx3

def speak(text, api_key=None, voice=None):
    engine = pyttsx3.init()
    if voice:
        voices = engine.getProperty('voices')
        # Try to set the requested voice if available
        for v in voices:
            if voice.lower() in v.name.lower():
                engine.setProperty('voice', v.id)
                break
    engine.say(text)
    engine.runAndWait() 