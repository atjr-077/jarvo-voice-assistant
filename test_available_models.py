import google.generativeai as genai

api_key = "AIzaSyDhMe-HN-BzEyP632i14GQa0u3LN-qMFNo"
genai.configure(api_key=api_key)

try:
    print("Listing available models...")
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"- {model.name}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
