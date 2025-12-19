from rapidfuzz import process
from functools import lru_cache
import datetime

# Map actions to possible user phrases
COMMANDS = {
    "increase_volume": [
        "increase volume", "turn up volume", "volume up", "raise volume", "louder"
    ],
    "decrease_volume": [
        "decrease volume", "turn down volume", "volume down", "lower volume", "quieter"
    ],
    "mute_audio": [
        "mute", "mute audio", "mute sound", "silence"
    ],
    "open_app": [
        "open", "launch", "start", "run"
    ],
    "close_app": [
        "close", "exit", "quit", "terminate"
    ],
    "set_timer": [
        "set timer", "remind me in", "alarm in"
    ],
    "tell_joke": [
        "tell me a joke", "make me laugh", "joke"
    ],
    "tell_time": [
        "what time is it", "tell me the time", "current time", "time", "clock"
    ],
    "tell_date": [
        "what's the date", "today's date", "current date", "date", "day", "today"
    ],
    "get_ip": [
        "what's my ip", "show my ip", "ip address"
    ],
    "generate_code": [
        "generate code for", "write code for", "create code for", "write a script to", "make a program that"
    ],
    "ask_ai": [
        "what is", "what are", "who is", "who are", "how do", "how does", "why", "when", 
        "where", "tell me about", "explain", "describe", "can you", "do you know"
    ],
    "stop_assistant": [
        "stop", "exit", "quit", "terminate", "shutdown", "goodbye", "bye"
    ],
    "media_play_pause": [
        "play", "pause", "resume", "stop music", "resume music"
    ],
    "media_next": [
        "next", "next song", "next track", "skip", "skip song"
    ],
    "media_prev": [
        "previous", "previous song", "previous track", "go back", "back"
    ],
    "system_lock": [
        "lock", "lock screen", "lock computer"
    ],
    "system_brightness_up": [
        "increase brightness", "brightness up", "brighter"
    ],
    "system_brightness_down": [
        "decrease brightness", "brightness down", "dimmer", "lower brightness"
    ],
    "system_recycle_bin": [
        "empty recycle bin", "empty trash", "clean trash", "clear recycle bin"
    ],
    "system_stats": [
        "cpu usage", "ram usage", "memory usage", "battery status", "system status", "how is my pc"
    ],
    "window_minimize": [
        "minimize all", "show desktop", "minimize windows", "hide windows"
    ],
    "window_switch": [
        "switch window", "alt tab", "switch app"
    ],
    "utility_coin": [
        "flip a coin", "heads or tails", "toss a coin"
    ],
    "utility_dice": [
        "roll a die", "roll a dice", "roll number"
    ],
    "play_youtube": [
        "play video", "play on youtube", "play song", "play music"
    ]
}

def match_intent(user_input):
    """Fuzzy match user input to a known action."""
    user_input = user_input.lower().strip()
    
    # specific override for dynamic "play ..." commands
    if user_input.startswith("play ") and len(user_input) > 5:
        # Avoid matching "play" (media_play_pause) if there's more text
        return "play_youtube"
        
    for action, phrases in COMMANDS.items():
        match, score, _ = process.extractOne(user_input, phrases)
        if score >= 75:
            return action
    return None

@lru_cache(maxsize=32)
def cached_web_search(query):
    """Cache web search results to avoid repeated API calls."""
    # Replace with your actual web search logic
    return f"Results for {query}"

def log_command(command, action):
    """Log the command and action with a timestamp to a file."""
    with open("jarvo_command_log.txt", "a", encoding="utf-8") as f:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"{timestamp} | Command: {command} | Action: {action}\n")