import speech_recognition as sr
from speech_recognition import Recognizer, Microphone, UnknownValueError, RequestError
# Load configuration (env variables like LIVEKIT_URL/API_KEY/SECRET)
import config  # noqa: F401
import random
import pyttsx3
import subprocess
import webbrowser
import sys
import argparse
import time
from speech import listen, speak, list_microphones, set_mic_index, set_status_callback, get_current_stt_engine
from actions import route_action
from utils import match_intent, log_command
import threading
from threading import Event
from assistant.state import INTERACTION_IN_PROGRESS

FOLLOW_UP_PROMPTS = [
    "What do you want me to do next?",
    "Anything else?",
    "What's the next task?",
]

def _speak_follow_up() -> None:
    phrase = random.choice(FOLLOW_UP_PROMPTS)
    speak(phrase)


def process_command(command: str) -> None:
    if not command:
        speak("No input detected. Please try again.")
        log_command(command, "no_input")
        _speak_follow_up()
        return
    action = match_intent(command)
    # Handle stop command explicitly to end the assistant gracefully
    if action == "stop_assistant":
        speak("Okay, stopping now. Goodbye!")
        log_command(command, action)
        STOP_EVENT.set()
        return
    if action:
        route_action(action, command)
        log_command(command, action)
        if not INTERACTION_IN_PROGRESS.is_set():
            _speak_follow_up()
    else:
        # Use AI as fallback for unknown commands
        try:
            from ai_conversation import ask_ai
            response = ask_ai(command)
            speak(response)
            log_command(command, "ai_fallback")
        except Exception as e:
            speak("Sorry, I didn't understand. Try rephrasing.")
            log_command(command, f"unknown_action: {e}")
        if not INTERACTION_IN_PROGRESS.is_set():
            _speak_follow_up()


STOP_EVENT: Event = Event()


def main():
    """Jarvo assistant entrypoint.

    Modes:
      - Default (no args): Voice loop
      - --text "...": Run a single typed command then exit
      - --interactive-text: Read typed commands in a loop
      - --wake-word: Use wake word detection mode
      - --direct: Direct listening without wake word
    """
    parser = argparse.ArgumentParser(description="Jarvo Assistant")
    parser.add_argument("--text", type=str, help="Run a single typed command and exit")
    parser.add_argument("--interactive-text", action="store_true", help="Run in interactive text mode")
    parser.add_argument("--list-mics", action="store_true", help="List available microphones and exit")
    parser.add_argument("--mic", type=int, help="Microphone device index to use")
    parser.add_argument("--wake-word", action="store_true", help="Use wake word detection mode")
    parser.add_argument("--direct", action="store_true", help="Direct listening without wake word")
    parser.add_argument("--status", action="store_true", help="Show current STT engine and microphone info")
    args = parser.parse_args()

    if args.list_mics:
        names = list_microphones()
        if not names:
            print("No microphones found.")
        else:
            for idx, name in enumerate(names):
                print(f"[{idx}] {name}")
        return

    if args.mic is not None:
        set_mic_index(args.mic)

    if args.status:
        print(f"Current STT Engine: {get_current_stt_engine()}")
        print(f"Available microphones:")
        mics = list_microphones()
        for i, mic in enumerate(mics):
            print(f"  [{i}] {mic}")
        return

    if args.text:
        print("Processing typed command...")
        process_command(args.text)
        return

    if args.interactive_text:
        print("Interactive text mode. Type 'exit' to quit.")
        while not STOP_EVENT.is_set():
            try:
                user_input = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()  # newline
                break
            if user_input.lower() in {"exit", "quit"}:
                break
            print("Processing...")
            # Run handling on a background thread to keep UI responsive if actions block
            threading.Thread(target=process_command, args=(user_input,), daemon=True).start()
        return

    # Set up status callback for better feedback
    def status_callback(status):
        print(f"[STATUS] {status}")
    
    set_status_callback(status_callback)

    # Voice mode with options
    if args.wake_word:
        print("Starting wake word mode. Say 'Jarvis' to activate...")
        from speech import listen_with_wake_word
        while not STOP_EVENT.is_set():
            if INTERACTION_IN_PROGRESS.is_set():
                time.sleep(0.2)
                continue
            command = listen_with_wake_word()
            if command:
                print("Processing...")
                threading.Thread(target=process_command, args=(command,), daemon=True).start()
    elif args.direct:
        print("Starting direct listening mode...")
        from speech import listen_direct
        while not STOP_EVENT.is_set():
            print("Listening...")
            if INTERACTION_IN_PROGRESS.is_set():
                time.sleep(0.2)
                continue
            command = listen_direct()
            if command:
                print("Processing...")
                threading.Thread(target=process_command, args=(command,), daemon=True).start()
    else:
        # Default: voice mode (uses config to determine wake word or direct)
        print("Starting voice mode...")
        while not STOP_EVENT.is_set():
            print("Listening...")
            # If another interactive flow is in progress (e.g., code-gen Q&A), wait
            if INTERACTION_IN_PROGRESS.is_set():
                time.sleep(0.2)
                continue
            command = listen()
            if command:
                print("Processing...")
                threading.Thread(target=process_command, args=(command,), daemon=True).start()

if __name__ == '__main__':
    main() 