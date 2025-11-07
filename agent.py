import os
from dotenv import load_dotenv
import google.generativeai as genai

# 🌐 Added import for translation
from googletrans import Translator  

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

# 🌐 Initialize Translator (Googletrans)
translator = Translator()

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

    # 🌐 Modified definition to accept optional 'lang' parameter
    def ask(self, user_message: str, lang: str = "en") -> str:
        """Send a message to Gemini and return the reply."""
        try:
            # 🌐 Translate user input to English if needed
            if lang != "en":
                try:
                    user_message = translator.translate(user_message, src=lang, dest="en").text
                except Exception as e:
                    print(f"⚠️ Translation error (input): {e}")

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

            # 🌐 Translate reply back to user's selected language
            if lang != "en":
                try:
                    reply = translator.translate(reply, src="en", dest=lang).text
                except Exception as e:
                    print(f"⚠️ Translation error (output): {e}")

            return reply

        except Exception as e:
            return f"⚠️ Error: {str(e)}"
