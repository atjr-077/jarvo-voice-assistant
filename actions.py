import os
import webbrowser
import datetime
import subprocess
import platform
from datetime import datetime
from speech import speak, listen
import threading
import time
import socket
from datetime import datetime
from speech import speak
import re
from utils import log_command
from assistant.state import INTERACTION_IN_PROGRESS
from contextlib import contextmanager
from ai_conversation import ask_ai, clear_conversation

# Existing actions
def open_chrome():
    try:
        os.startfile("chrome.exe")
    except Exception:
        webbrowser.open("https://www.google.com")

def open_notepad():
    os.startfile("notepad.exe")

def search_google(query):
    webbrowser.open(f"https://www.google.com/search?q={query}")

def tell_time():
    now = datetime.datetime.now()
    return f"The current time is {now.strftime('%I:%M %p')}"

# New actions
def open_app(app_name):
    """Try to open an application and handle errors on Windows.
    Accepts names with or without .exe, returns a status string.
    """
    import subprocess
    import os
    base_name = app_name.strip()
    if base_name.lower().endswith('.exe'):
        app_exec = base_name
    else:
        app_exec = base_name + ".exe"
    common_paths = {
        "notepad": r"C:\\Windows\\System32\\notepad.exe",
        "calc": r"C:\\Windows\\System32\\calc.exe",
        "mspaint": r"C:\\Windows\\System32\\mspaint.exe",
        "cmd": r"C:\\Windows\\System32\\cmd.exe",
    }

    # Candidate install paths for popular browsers on Windows
    browser_candidates = {
        "chrome": [
            r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            r"C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
        ],
        "google": [
            r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            r"C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
        ],
        "msedge": [
            r"C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
            r"C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
        ],
        "edge": [
            r"C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
            r"C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
        ],
        "firefox": [
            r"C:\\Program Files\\Mozilla Firefox\\firefox.exe",
            r"C:\\Program Files (x86)\\Mozilla Firefox\\firefox.exe",
        ],
    }
    try:
        print(f"Trying to open: {app_exec}")
        subprocess.Popen(app_exec)
        speak(f"Opened {base_name}")
        log_command(f"open {base_name}", "open_app")
        return f"Opened {base_name}"
    except FileNotFoundError:
        key = base_name.strip().lower()
        # Try common system paths
        if key in common_paths:
            full_path = common_paths[key]
            print(f"Trying full path: {full_path}")
            try:
                subprocess.Popen(full_path)
                speak(f"Opened {base_name}")
                log_command(f"open {base_name}", "open_app_fullpath")
                return f"Opened {base_name}"
            except Exception as e:
                speak(f"Failed to open {base_name}.")
                log_command(f"open {base_name}", f"open_app_fullpath_failed: {e}")
                return f"Failed to open {base_name}"

        # Try known browser installation paths
        if key in browser_candidates:
            import os as _os
            for candidate in browser_candidates[key]:
                if _os.path.exists(candidate):
                    print(f"Trying browser path: {candidate}")
                    try:
                        subprocess.Popen(candidate)
                        speak(f"Opened {base_name}")
                        log_command(f"open {base_name}", "open_app_browser_path")
                        return f"Opened {base_name}"
                    except Exception as e:
                        continue
            # As a last resort for chrome/google, open Google homepage in default browser
            if key in ("chrome", "google"):
                webbrowser.open("https://www.google.com")
                speak("Opened Google in your default browser")
                log_command(f"open {base_name}", "open_app_google_web")
                return "Opened Google in default browser"

        speak(f"Failed to open {base_name}.")
        log_command(f"open {base_name}", "open_app_not_found")
        return f"Failed to open {base_name}"
    except Exception as e:
        speak(f"Failed to open {base_name}.")
        log_command(f"open {base_name}", f"open_app_failed: {e}")
        return f"Failed to open {base_name}"

def play_youtube(query):
    url = f"https://www.youtube.com/results?search_query={query}"
    webbrowser.open(url)
    speak(f"Playing {query} on YouTube")
    return f"Played {query} on YouTube"

def search_wikipedia(query):
    webbrowser.open(f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}")
    return f"Searching Wikipedia for {query}."

def shutdown_computer():
    os.system("shutdown /s /t 1")
    return "Shutting down the computer."

def control_volume(action, value=None):
    """Control system volume: action can be 'up', 'down', 'mute', 'set'. Value is % for 'set'."""
    try:
        if platform.system() == 'Windows':
            import ctypes
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            if action == 'mute':
                volume.SetMute(1, None)
                return 'Muted volume.'
            elif action == 'up':
                current = volume.GetMasterVolumeLevelScalar()
                volume.SetMasterVolumeLevelScalar(min(current + 0.1, 1.0), None)
                return 'Increased volume.'
            elif action == 'down':
                current = volume.GetMasterVolumeLevelScalar()
                volume.SetMasterVolumeLevelScalar(max(current - 0.1, 0.0), None)
                return 'Decreased volume.'
            elif action == 'set' and value is not None:
                volume.SetMasterVolumeLevelScalar(float(value)/100, None)
                return f'Set volume to {value}%.'
        return 'Volume control not supported on this OS.'
    except Exception as e:
        return f'Error controlling volume: {e}'

def take_screenshot():
    """Take a screenshot and save to Desktop with timestamp."""
    try:
        from PIL import ImageGrab
        dt = datetime.now().strftime('%Y%m%d_%H%M%S')
        path = os.path.join(os.path.expanduser('~'), 'Desktop', f'screenshot_{dt}.png')
        img = ImageGrab.grab()
        img.save(path)
        return f'Screenshot saved to {path}'
    except Exception as e:
        return f'Error taking screenshot: {e}'

def get_news_headlines():
    """Fetch and return top news headlines (uses NewsAPI, mock for now)."""
    # You can use requests and a real API key for NewsAPI.org
    try:
        import requests
        api_key = 'demo'  # Replace with your NewsAPI key
        url = f'https://newsapi.org/v2/top-headlines?country=us&apiKey={api_key}'
        r = requests.get(url)
        data = r.json()
        if 'articles' in data:
            headlines = [a['title'] for a in data['articles'][:5]]
            return 'Top news: ' + '; '.join(headlines)
        return 'Could not fetch news.'
    except Exception as e:
        return f'Error fetching news: {e}'

def get_weather(location=None):
    """Stub for weather retrieval (to be implemented)."""
    speak("Weather feature coming soon.")
    log_command(f"weather {location}", "get_weather_stub")
    return "Weather feature coming soon."

def get_stock_price(ticker='AAPL'):
    """Fetch and return current stock price (uses Yahoo Finance, mock for now)."""
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker)
        price = stock.info.get('regularMarketPrice')
        if price:
            return f'{ticker} stock price: ${price}'
        return f'Could not fetch stock price for {ticker}.'
    except Exception as e:
        return f'Error fetching stock price: {e}'

def set_timer(seconds):
    """Set a timer and notify when done."""
    def timer():
        time.sleep(seconds)
        speak("Timer finished!")
    threading.Thread(target=timer, daemon=True).start()

def tell_joke():
    """Tell a random joke."""
    jokes = [
        "Why don’t skeletons fight each other? They don’t have the guts.",
        "I have a stepladder because my real ladder left when I was a kid.",
        "Why don’t graveyards ever get overcrowded? People are dying to get in.",
        "My boss told me to have a good day, so I went home.",
        "Why don’t cannibals eat clowns? Because they taste funny.",
        "I’m great at multitasking. I can waste time, be unproductive, and procrastinate all at once.",
        "Why did the scarecrow win an award? Because he was outstanding in his field.",
        "Parallel lines have so much in common. It’s a shame they’ll never meet.",
        "I threw a boomerang a few years ago. I now live in constant fear.",
        "I asked my date to meet me at the gym, but she never showed up. I guess the two of us aren’t going to work out."
    ]
    import random
    joke = random.choice(jokes)
    speak(joke)
    return joke

def get_ip():
    """Get the local IP address."""
    ip = socket.gethostbyname(socket.gethostname())
    speak(f"Your IP address is {ip}")
    return ip

# --- New Functionality Helpers ---

def control_media(action):
    """Control media playback."""
    try:
        import pyautogui
        if action == "play_pause":
            pyautogui.press("playpause")
            return "Toggled media playback."
        elif action == "next":
            pyautogui.press("nexttrack")
            return "Skipped to next track."
        elif action == "prev":
            pyautogui.press("prevtrack")
            return "Returned to previous track."
    except Exception as e:
        return f"Error controlling media: {e}"

def control_brightness(action):
    """Control screen brightness."""
    try:
        import screen_brightness_control as sbc
        current = sbc.get_brightness(display=0)[0]
        if action == "up":
            new_val = min(current + 20, 100)
            sbc.set_brightness(new_val)
            speak(f"Brightness increased to {new_val} percent.")
        elif action == "down":
            new_val = max(current - 20, 0)
            sbc.set_brightness(new_val)
            speak(f"Brightness decreased to {new_val} percent.")
    except Exception as e:
        speak("Failed to adjust brightness.")
        return f"Error adjusting brightness: {e}"

def lock_screen():
    """Lock the workstation."""
    try:
        import ctypes
        ctypes.windll.user32.LockWorkStation()
        return "Locked the screen."
    except Exception as e:
        return f"Error locking screen: {e}"

def empty_recycle_bin():
    """Empty the recycle bin."""
    try:
        import winshell
        winshell.recycle_bin().empty(confirm=False, show_progress=False, sound=True)
        speak("Recycle bin emptied.")
        return "Recycle bin emptied."
    except Exception as e:
        return f"Error emptying recycle bin: {e}"

def get_system_stats(stat_type):
    """Get system stat info."""
    try:
        import psutil
        if "cpu" in stat_type:
            usage = psutil.cpu_percent(interval=1)
            speak(f"CPU usage is at {usage} percent.")
        elif "ram" in stat_type or "memory" in stat_type:
            mem = psutil.virtual_memory()
            speak(f"RAM usage is at {mem.percent} percent.")
        elif "battery" in stat_type:
            battery = psutil.sensors_battery()
            if battery:
                plugged = "plugged in" if battery.power_plugged else "on battery"
                speak(f"Battery is at {battery.percent} percent and {plugged}.")
            else:
                speak("No battery detected.")
    except Exception as e:
        return f"Error getting stats: {e}"

def window_manager(action):
    """Manage windows."""
    try:
        import pyautogui
        if action == "minimize":
            pyautogui.hotkey('win', 'd')
            return "Toggled desktop."
        elif action == "switch":
            pyautogui.hotkey('alt', 'tab')
            return "Switched window."
    except Exception as e:
        return f"Error managing windows: {e}"

def run_utility(util_type):
    import random
    if util_type == "coin":
        result = random.choice(["Heads", "Tails"])
        speak(f"It's {result}!")
        return result
    elif util_type == "dice":
        result = random.randint(1, 6)
        speak(f"You rolled a {result}.")
        return str(result)

def route_action(action, command):
    """Route the action to the correct function."""
    if action == "stop_assistant":
        speak("Okay, stopping now. Goodbye!")
        log_command(command, "stop_assistant")
        import sys
        sys.exit(0)
    if action == "increase_volume":
        import ctypes
        for _ in range(5):
            ctypes.windll.user32.keybd_event(0xAF, 0, 0, 0)
        speak("Volume increased.")
    elif action == "decrease_volume":
        import ctypes
        for _ in range(5):
            ctypes.windll.user32.keybd_event(0xAE, 0, 0, 0)
        speak("Volume decreased.")
    elif action == "mute_audio":
        import ctypes
        ctypes.windll.user32.keybd_event(0xAD, 0, 0, 0)
        speak("Volume muted.")
    elif action == "open_app":
        # Extract app name from command, removing filler words
        app_name = command.lower()
        # Remove action words
        for word in ["open", "launch", "start", "run"]:
            app_name = app_name.replace(word, "")
        # Remove filler words
        for filler in ["to", "the", "a", "an", "my", "please"]:
            app_name = app_name.replace(filler, "")
        app_name = app_name.strip()
        
        # Handle common variations
        if "google" in app_name or "chrome" in app_name:
            app_name = "chrome"
        elif "edge" in app_name:
            app_name = "edge"
        elif "firefox" in app_name:
            app_name = "firefox"
        elif "notepad" in app_name:
            app_name = "notepad"
        elif "calculator" in app_name or "calc" in app_name:
            app_name = "calc"
        
        result = open_app(app_name)
        return result
    elif action == "close_app":
        app_name = command.replace("close", "").replace("exit", "").replace("quit", "").strip()
        import os
        os.system(f"taskkill /im {app_name}.exe /f")
        speak(f"Closed {app_name}")
    elif action == "set_timer":
        import re
        match = re.search(r'(\d+)', command)
        seconds = int(match.group(1)) if match else 60
        set_timer(seconds)
    elif action == "tell_joke":
        tell_joke()
    elif action == "tell_time":
        import datetime
        now = datetime.datetime.now().strftime("%I:%M %p")
        speak(f"The time is {now}")
    elif action == "tell_date":
        import datetime
        today = datetime.datetime.now().strftime("%A, %B %d, %Y")
        speak(f"Today is {today}")
    elif action == "get_ip":
        get_ip()
    elif action == "generate_code":
        prefixes = [
            "generate code for",
            "write code for",
            "create code for",
            "write a script to",
            "make a program that",
        ]
        lower_cmd = command.lower().strip()
        prompt = None
        for p in prefixes:
            if lower_cmd.startswith(p):
                prompt = lower_cmd[len(p):].strip()
                break
        if not prompt:
            # Fallback: try to remove any prefix occurrence
            for p in prefixes:
                if p in lower_cmd:
                    prompt = lower_cmd.split(p, 1)[1].strip()
                    break
        if not prompt:
            speak("What should I generate code for?")
            return "No prompt provided for code generation."

        # --- Ask follow-up questions to clarify (pause main mic during Q&A) ---
        with interaction_in_progress():
            language = _ask_with_default(
                question="Which programming language should I use? You can say Python, JavaScript, or something else.",
                default_answer="Python",
            )
            filename = _ask_with_default(
                question="What file name should I save it as? You can say for example generated_code dot py.",
                default_answer=_default_filename_for_language(language),
            )
            extra = _ask_optional(
                question="Any extra requirements? For example libraries to use or constraints.",
            )

        full_prompt = prompt
        if extra:
            full_prompt = f"{prompt}. Additional requirements: {extra}."
        return generate_code_with_gemini(full_prompt, filename=filename, language=language)
    elif action == "ask_ai":
        # Use AI to answer the question
        response = ask_ai(command)
        speak(response)
        log_command(command, "ask_ai")
        return response
    # --- New Route Handlers ---
    elif action == "play_youtube":
        # Extract query
        query = command.lower().replace("play", "", 1).strip()
        # Remove filler words
        for filler in ["song", "video", "music", "on youtube"]:
            query = query.replace(filler, "")
        query = query.strip()
        
        if not query:
            # Fallback to just resume if no query
            control_media("play_pause")
            speak("Resumed playback.")
        else:
            play_youtube(query)
    elif action == "media_play_pause":
        control_media("play_pause")
    elif action == "media_next":
        control_media("next")
    elif action == "media_prev":
        control_media("prev")
    elif action == "system_lock":
        lock_screen()
    elif action == "system_brightness_up":
        control_brightness("up")
    elif action == "system_brightness_down":
        control_brightness("down")
    elif action == "system_recycle_bin":
        empty_recycle_bin()
    elif action == "system_stats":
        get_system_stats(command)
    elif action == "window_minimize":
        window_manager("minimize")
    elif action == "window_switch":
        window_manager("switch")
    elif action == "utility_coin":
        run_utility("coin")
    elif action == "utility_dice":
        run_utility("dice")
    else:
        speak("Sorry, I didn't understand that command. Please try again or rephrase.")
    
def _ask_with_default(question: str, default_answer: str) -> str:
    """Ask a question via voice, return answer or default if no clear response."""
    for _ in range(2):
        speak(question)
        ans = listen()
        if ans:
            return ans.strip()
    return default_answer


def _ask_optional(question: str) -> str | None:
    """Ask a question; return answer or None if not captured."""
    speak(question)
    ans = listen()
    return ans.strip() if ans else None


def _default_filename_for_language(language: str) -> str:
    lang = (language or "").strip().lower()
    if lang.startswith("py"):
        return "generated_code.py"
    if lang in ("javascript", "js"):
        return "generated_code.js"
    if lang in ("typescript", "ts"):
        return "generated_code.ts"
    if lang in ("java",):
        return "GeneratedCode.java"
    if lang in ("c#", "csharp"):
        return "GeneratedCode.cs"
    if lang in ("c++", "cpp"):
        return "generated_code.cpp"
    if lang in ("go", "golang"):
        return "generated_code.go"
    if lang in ("rust",):
        return "generated_code.rs"
    return "generated_code.txt"


@contextmanager
def interaction_in_progress():
    """Context manager to signal interactive Q&A is running, pausing main mic loop."""
    try:
        INTERACTION_IN_PROGRESS.set()
        yield
    finally:
        INTERACTION_IN_PROGRESS.clear()


def generate_code_with_gemini(prompt, filename="generated_code.py", language: str = "Python"):
    """
    Generate code using Gemini AI and write it to a file.
    """
    import os
    try:
        from config import get_gemini_api_key  # prefer config default/env
        api_key = get_gemini_api_key()
    except Exception:
        api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        speak("Gemini API key is missing. Please set GEMINI_API_KEY and try again.")
        return "Missing GEMINI_API_KEY"
    try:
        import google.generativeai as genai
    except Exception:
        speak("Google Generative AI library not installed. Please install google-generativeai.")
        return "google-generativeai not installed"

    # Set your Gemini API key
    genai.configure(api_key=api_key)

    # Create the model (prefer latest; fallback to older names)
    model_names = [
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-pro",
    ]
    last_err = None
    response = None
    for _model_name in model_names:
        try:
            model = genai.GenerativeModel(_model_name)
            response = model.generate_content(f"Write a {prompt} in {language}.")
            break
        except Exception as e:
            last_err = e
            continue
    if response is None:
        speak(f"Code generation failed: {last_err}")
        return f"Code generation failed: {last_err}"

    # Extract code from response (may need to parse markdown)
    code = response.text
    # Optionally, extract code block only:
    import re
    match = re.search(r"```(?:python)?\n(.*?)```", code, re.DOTALL)
    code_content = match.group(1) if match else code

    # Write code to file
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(code_content)
        speak(f"Code written to {filename}")
        return f"Code written to {filename}"
    except Exception as e:
        speak(f"Failed to write file: {e}")
        return f"Failed to write file: {e}"