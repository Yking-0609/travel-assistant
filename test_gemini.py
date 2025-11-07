from agent import GeminiAssistant

print("Fetching available Gemini models and testing response...\n")

try:
    assistant = GeminiAssistant()
    print(f"✅ Greeting: {assistant.greet()}\n")
except Exception as e:
    print(f"❌ Failed to initialize GeminiAssistant: {e}")
    exit(1)

# Test a sample chat
test_message = "Hello, Gemini! Can you give me a travel tip for India?"
print(f"Sending test message: {test_message}")

reply = assistant.ask(test_message)
print(f"✅ Gemini reply: {reply}")
