from ai_conversation import GeminiConversation

try:
    conv = GeminiConversation()
    result = conv.ask("What is 2+2?")
    print(f"Success! Answer: {result}")
except Exception as e:
    print(f"Error: {type(e).__name__}")
    print(f"Message: {str(e)}")
    import traceback
    traceback.print_exc()
