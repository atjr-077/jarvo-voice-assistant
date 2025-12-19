import requests

def get_intent_from_ollama(user_text, model="llama2"):
    url = "http://localhost:11434/api/generate"
    prompt = f"""
You are a local AI desktop assistant. Your job is to interpret the user's spoken commands and return a single, valid JSON object describing the system-level action to take. 
NEVER explain, NEVER add extra text, ONLY output a JSON object. 
NEVER default to searching the web unless the user explicitly says things like: "search Google for...", "look this up online", "search the web for...".

Examples:
User: Decrease the volume
{{"action": "decrease_volume"}}

User: Open Notepad
{{"action": "open_app", "app_name": "notepad"}}

User: Search Google for Python tutorials
{{"action": "search_google", "query": "Python tutorials"}}

User: Mute the audio
{{"action": "mute_audio"}}

User: Close calculator
{{"action": "close_app", "app_name": "calculator"}}

User: What time is it?
{{"action": "tell_time"}}

User: {user_text}
"""
    data = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(url, json=data)
    result = response.json()
    # The model's response will be in result['response']
    # Try to extract the JSON part
    import re, json as pyjson
    match = re.search(r'\{[\s\S]*\}', result['response'])
    if match:
        try:
            return pyjson.loads(match.group(0))
        except Exception:
            return {"error": "Could not parse JSON from LLM response.", "raw": result['response']}
    return {"error": "No JSON found in LLM response.", "raw": result['response']} 