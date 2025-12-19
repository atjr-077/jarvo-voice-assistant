import google.generativeai as genai

api_key = "AIzaSyDhMe-HN-BzEyP632i14GQa0u3LN-qMFNo"
genai.configure(api_key=api_key)

print("Listing available models...")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"- {m.name}")

print("\nTrying gemini-1.5-flash...")
try:
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Say hello in one sentence")
    print(f"Success with gemini-1.5-flash: {response.text}")
except Exception as e:
    print(f"Error with gemini-1.5-flash: {e}")

print("\nTrying gemini-1.5-pro...")
try:
    model = genai.GenerativeModel('gemini-1.5-pro')
    response = model.generate_content("Say hello in one sentence")
    print(f"Success with gemini-1.5-pro: {response.text}")
except Exception as e:
    print(f"Error with gemini-1.5-pro: {e}")
