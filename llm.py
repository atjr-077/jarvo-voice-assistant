import requests
import json

def ask_gpt(prompt, api_key=None, model="llama3"):
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    response = requests.post(url, json=payload, stream=True)
    response.raise_for_status()
    full_response = ""
    for line in response.iter_lines():
        if line:
            data = json.loads(line.decode("utf-8"))
            # Ollama streams partial responses, so we concatenate them
            if "message" in data and "content" in data["message"]:
                full_response += data["message"]["content"]
            elif "response" in data:
                full_response += data["response"]
    return full_response.strip() 