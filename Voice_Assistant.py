import speech_recognition as sr

recognizer = sr.Recognizer()

try:
    with sr.Microphone() as source:
        print("Adjusting for ambient noise...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Say something:")
        audio = recognizer.listen(source, timeout=5)
        print("Processing...")
        text = recognizer.recognize_google(audio)
        print("You said:", text)
except sr.UnknownValueError:
    print("Could not understand the audio")
except sr.RequestError as e:
    print("Could not request results from Google Speech Recognition service; {0}".format(e))
except sr.WaitTimeoutError:
    print("No speech detected within the timeout period")
except Exception as e:
    print("An error occurred: {0}".format(e))
