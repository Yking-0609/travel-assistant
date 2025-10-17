import os
from dotenv import load_dotenv
import google.generativeai as genai

# -----------------------------------------------------------
# Load API key from .env
# -----------------------------------------------------------
# Ensure .env is in the same folder as agent.py
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# ✅ Look up the variable by name, not by the key itself
api_key = os.getenv("GOOGLE_API_KEY")
print("DEBUG GOOGLE_API_KEY:", api_key)  # Debugging – remove later

if not api_key or not api_key.strip():
    raise ValueError("❌ GOOGLE_API_KEY not found in environment. Please set it in .env")

# Configure Gemini client
genai.configure(api_key=api_key)


# -----------------------------------------------------------
# Gemini Travel Assistant
# -----------------------------------------------------------
class GeminiAssistant:
    def __init__(self, model_name="gemini-2.5-flash"):  # or "gemini-1.5-pro"
        self.model = genai.GenerativeModel(model_name)
        self.conversation = []

    def greet(self) -> str:
        """Return a welcome message."""
        return "Hello! 👋 I'm your travel assistant by Atlast Tours and Travels. Where would you like to go?"

    def ask(self, user_message: str) -> str:
        """Send a message to Gemini and return the reply."""
        try:
            # Save the user message to the conversation history
            self.conversation.append({"role": "user", "content": user_message})

            # Build conversation context for the model
            context = "\n".join(
                f"{msg['role'].capitalize()}: {msg['content']}"
                for msg in self.conversation
            )

            # Generate Gemini response
            response = self.model.generate_content(
                f"You are a helpful travel assistant. "
                f"Provide friendly travel advice, destination guides, and itineraries.\n\n{context}"
            )

            reply = response.text.strip()

            # Save the assistant's reply
            self.conversation.append({"role": "assistant", "content": reply})

            return reply

        except Exception as e:
            return f"⚠️ Error: {str(e)}"
