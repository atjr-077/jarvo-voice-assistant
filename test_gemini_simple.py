import google.generativeai as genai

api_key = "AIzaSyDhMe-HN-BzEyP632i14GQa0u3LN-qMFNo"
genai.configure(api_key=api_key)

try:
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content("Say hello")
    print(f"Success: {response.text}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
