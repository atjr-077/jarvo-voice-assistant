import google.generativeai as genai
from config import get_gemini_api_key

api_key = get_gemini_api_key()
print(f"Using API Key: {api_key[:5]}...{api_key[-5:]}")

genai.configure(api_key=api_key)

try:
    print("Testing gemini-2.5-flash...")
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content("Hello")
    print(f"Success! Response: {response.text}")
except Exception as e:
    print(f"Error with gemini-2.5-flash: {e}")
    
    print("\nTrying fallback to gemini-1.5-flash...")
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Hello")
        print(f"Success with 1.5-flash! Response: {response.text}")
    except Exception as e2:
         print(f"Error with gemini-1.5-flash: {e2}")
         
    print("\nListing available models:")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(m.name)
    except Exception as e3:
        print(f"Error listing models: {e3}")
