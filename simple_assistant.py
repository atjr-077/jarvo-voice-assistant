import speech_recognition as sr
import webbrowser
import os
from datetime import datetime

# Function that executes actions
def assistant(command):
    if "open youtube" in command:
        print("Opening YouTube...")
        webbrowser.open("https://youtube.com")
    elif "open google" in command:
        print("Opening Google...")
        webbrowser.open("https://google.com")
    elif "play music" in command:
        print("Playing music...")
        # This will try to open Windows Media Player
        os.system("start wmplayer")
    elif "time" in command:
        time_now = datetime.now().strftime("%H:%M:%S")
        print("Current time:", time_now)
    else:
        print("Sorry, I don't know how to do that yet.")

# Function to listen for commands
def listen():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        # Light ambient noise calibration for better results
        try:
            r.adjust_for_ambient_noise(source, duration=0.5)
        except Exception:
            pass
        audio = r.listen(source)

        try:
            command = r.recognize_google(audio).lower()
            print("You said:", command)
            assistant(command)
        except sr.UnknownValueError:
            print("Sorry, I did not understand.")
        except sr.RequestError:
            print("Could not request results, check your internet connection.")

# Main loop
if __name__ == "__main__":
    try:
        while True:
            listen()
    except KeyboardInterrupt:
        print("\nExiting.")



