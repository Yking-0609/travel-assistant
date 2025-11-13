import os
from dotenv import load_dotenv
import google.generativeai as genai
# ❌ Removed: from langdetect import detect, DetectorFactory, lang_detect_exception (This caused the crash)

# --- Load environment variables ---
load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    # Essential check to ensure your GOOGLE_API_KEY is correctly set on Render
    raise ValueError("GOOGLE_API_KEY not found. Set it in your environment variables or .env file.")

# --- Configure Gemini API ---
genai.configure(api_key=API_KEY)

class GeminiAssistant:
    def __init__(self):
        try:
            # Using the latest working Gemini model
            self.model = genai.GenerativeModel("models/gemini-2.5-flash")
            print("✅ Using model: gemini-2.5-flash")
        except Exception as e:
            # This will trigger the FATAL ERROR in app.py if the API key or config fails
            raise RuntimeError(f"Error initializing Gemini model: {e}")

        self.history = []

    def greet(self):
        """Friendly multilingual greeting."""
        return "👋 Namaste! Welcome to **Atlast Travel Assistant**. Where would you like to go today? (We cover destinations worldwide!)"
    
    def ask(self, message):
        """Main logic - fully relies on Gemini for language detection and response."""
        if not message.strip():
            return "Please enter a message."
        
        # --- Language is handled *entirely* by the prompt and Gemini ---
        print(f"🌍 Relying on Gemini to detect and respond in the user's language.")

        # --- Prepare context and prompt ---
        self.history.append({"role": "user", "content": message})
        context = "\n".join(f"{h['role']}: {h['content']}" for h in self.history[-6:])

        # 🎯 Prompt Instruction: Simple, clear instruction for the model to handle multilingual reply.
        prompt = (
            f"You are **Atlast Travel Assistant** — a helpful, polite AI specializing in **global travel**.\n"
            f"**STRICTLY** analyze the user's input language and respond entirely in that same language.\n"
            f"If the input is short or ambiguous (like a single word destination), assume it's a travel query and be helpful.\n"
            f"If the question is about travel, give detailed and polite suggestions for destinations worldwide.\n"
            f"Context:\n{context}\n\nUser: {message}"
        )

        # --- Generate response ---
        try:
            response = self.model.generate_content(prompt)
            reply = getattr(response, "text", None) or "Sorry, I couldn’t generate a reply."

            # Store the response for history context
            self.history.append({"role": "assistant", "content": reply})
            return reply.strip()

        except Exception as e:
            # Catching and reporting the API error is crucial for debugging
            print(f"Gemini API error: {e}")
            return "⚠️ Sorry, I encountered an issue with the Gemini API. Please try again later."