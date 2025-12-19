import tkinter as tk
from tkinter import scrolledtext
import threading
import os
import webbrowser
import subprocess

from listener import listen
from actions import open_app, search_google, play_youtube
from speech import speak
from llm_intent import get_intent_from_ollama

APP_PATHS = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "chrome": "chrome.exe",
    "firefox": "firefox.exe",
    "edge": "msedge.exe",
    "word": "winword.exe",
    "excel": "excel.exe",
    "powerpoint": "powerpnt.exe",
    "paint": "mspaint.exe",
    "command prompt": "cmd.exe",
    "explorer": "explorer.exe",
    "outlook": "outlook.exe",
    "onenote": "onenote.exe",
    "vlc": "vlc.exe",
    "spotify": "spotify.exe",
    "zoom": "zoom.exe",
    "teams": "teams.exe",
    "discord": "discord.exe",
    "skype": "skype.exe",
    "photoshop": "photoshop.exe",
    "adobe reader": "acrord32.exe",
    "snipping tool": "SnippingTool.exe",
    "task manager": "Taskmgr.exe",
    "control panel": "control.exe",
    "settings": "ms-settings:",
    "windows security": "windowsdefender:",
    "powershell": "powershell.exe",
    "paint 3d": "mspaint.exe",
    "wordpad": "wordpad.exe",
    "camera": "microsoft.windows.camera:",
    "instagram": "https://www.instagram.com/"
}

import datetime
import ctypes

class VoiceAssistantGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Voice Assistant")
        self.root.geometry("400x500")
        self.root.resizable(False, False)
        self.listening = False

        # Microphone button
        self.mic_button = tk.Button(root, text="🎤 Start Listening", command=self.toggle_listen, font=("Arial", 16))
        self.mic_button.pack(pady=10)

        # Transcribed text
        self.transcribed_label = tk.Label(root, text="You said:", font=("italic", 12))
        self.transcribed_label.pack()
        self.transcribed_text = tk.Entry(root, font=("Arial", 14), width=40, state='readonly', justify='center')
        self.transcribed_text.pack(pady=5)

        # Assistant response label
        self.response_label = tk.Label(root, text="", font=("Arial", 12), fg="blue")
        self.response_label.pack(pady=5)

        # Log area
        self.log_area = scrolledtext.ScrolledText(root, width=45, height=15, font=("Arial", 10), state='disabled')
        self.log_area.pack(pady=10)

    def toggle_listen(self):
        if not self.listening:
            self.listening = True
            self.mic_button.config(text="🛑 Stop Listening")
            threading.Thread(target=self.listen_loop, daemon=True).start()
        else:
            self.listening = False
            self.mic_button.config(text="🎤 Start Listening")

    def listen_loop(self):
        speak("Listening. Press stop to end.")
        while self.listening:
            command = listen()
            self.update_transcribed(command)
            if command:
                action_result, response = self.handle_command(command)
                self.log_action(action_result)
                self.update_response(response)
            else:
                self.update_response("Sorry, I didn't catch that.")
            # Wait a bit before next listen to avoid rapid looping
            self.root.after(1000)
        self.update_response("Stopped listening.")

    def handle_command(self, command):
        intent = get_intent_from_ollama(command)
        if "action" not in intent:
            speak("Sorry, I couldn't understand your request.")
            return "Unknown command.", "Sorry, I couldn't understand your request."
        # Now act on the intent['action'] and any parameters
        action = intent["action"]
        if action == "open_app":
            app = intent.get("app_name", "")
            result = open_app(app + ".exe")
            return result, result
        elif action == "decrease_volume":
            try:
                import ctypes
                for _ in range(5):
                    ctypes.windll.user32.keybd_event(0xAE, 0, 0, 0)  # VK_VOLUME_DOWN
                speak("Volume decreased.")
                return "Decreased volume.", "Volume decreased."
            except Exception:
                speak("Sorry, I couldn't decrease the volume.")
                return "Failed to decrease volume.", "Sorry, I couldn't decrease the volume."
        elif action == "increase_volume":
            try:
                import ctypes
                for _ in range(5):
                    ctypes.windll.user32.keybd_event(0xAF, 0, 0, 0)  # VK_VOLUME_UP
                speak("Volume increased.")
                return "Increased volume.", "Volume increased."
            except Exception:
                speak("Sorry, I couldn't increase the volume.")
                return "Failed to increase volume.", "Sorry, I couldn't increase the volume."
        elif action == "mute_audio":
            try:
                import ctypes
                ctypes.windll.user32.keybd_event(0xAD, 0, 0, 0)  # VK_VOLUME_MUTE
                speak("Volume muted.")
                return "Muted volume.", "Volume muted."
            except Exception:
                speak("Sorry, I couldn't mute the volume.")
                return "Failed to mute volume.", "Sorry, I couldn't mute the volume."
        elif action == "close_app":
            app = intent.get("app_name", "")
            import os
            os.system(f"taskkill /im {app}.exe /f")
            speak(f"Closed {app}.")
            return f"Closed {app}.", f"Closed {app}."
        elif action == "search_google":
            query = intent.get("query", "")
            result = search_google(query)
            return result, result
        elif action == "tell_time":
            import datetime
            now = datetime.datetime.now().strftime("%I:%M %p")
            speak(f"The time is {now}")
            return f"Told the time: {now}", f"The time is {now}"
        elif action == "tell_date":
            import datetime
            today = datetime.datetime.now().strftime("%A, %B %d, %Y")
            speak(f"Today is {today}")
            return f"Told the date: {today}", f"Today is {today}"
        else:
            speak("Sorry, I don't know how to do that yet.")
            return "Unknown command.", "Sorry, I don't know how to do that yet."

    def update_transcribed(self, text):
        self.transcribed_text.config(state='normal')
        self.transcribed_text.delete(0, tk.END)
        self.transcribed_text.insert(0, text)
        self.transcribed_text.config(state='readonly')

    def log_action(self, action):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, action + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def update_response(self, response):
        self.response_label.config(text=response)

if __name__ == "__main__":
    root = tk.Tk()
    app = VoiceAssistantGUI(root)
    root.mainloop() 