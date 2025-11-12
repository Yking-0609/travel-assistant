import os
import requests
from dotenv import load_dotenv
import google.generativeai as genai
# Removed langdetect and related imports to prevent crashes on complex inputs
from langdetect import DetectorFactory # Keep only for seeding if necessary, but remove detect

# --- Load environment variables ---
load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    # This check ensures your API key is configured correctly before the app starts
    raise ValueError("GOOGLE_API_KEY not found. Set it in your environment variables or .env file.")

# --- Configure Gemini API ---
genai.configure(api_key=API_KEY)

# --- External translation servers (keeping this for the _translate method, even if unused) ---
SERVERS = [
    "https://translate.argosopentech.com",
    "https://libretranslate.de",
    "https://translate.terraprint.co",
]

class GeminiAssistant:
    def __init__(self):
        try:
            # Using the latest working Gemini model
            self.model = genai.GenerativeModel("models/gemini-2.5-flash")
            print("✅ Using model: gemini-2.5-flash")
        except Exception as e:
            raise RuntimeError(f"Error initializing Gemini model: {e}")

        self.history = []

    def greet(self):
        """Friendly multilingual greeting."""
        return "👋 Namaste! Welcome to **Atlast Travel Assistant**. Where would you like to go today? (We cover destinations worldwide!)"

    def _translate(self, text, target):
        """Fallback translation helper (kept for safety, but not used in ask())."""
        for base in SERVERS:
            try:
                r = requests.post(
                    f"{base}/translate",
                    json={"q": text, "source": "auto", "target": target, "format": "text"},
                    timeout=6,
                )
                if r.status_code == 200:
                    return r.json().get("translatedText", text)
            except Exception:
                continue
        return text

    def ask(self, message):
        """Main logic — fully relies on Gemini for language detection and response."""
        if not message.strip():
            return "Please enter a message."
        
        # --- Language is now handled *entirely* by the prompt and Gemini ---
        # The Python code no longer attempts manual detection, eliminating the crash point.
        lang = "en" # Default internal reference, but not used for prompt instruction.

        print(f"🌍 Relying on Gemini to detect and respond in the user's language.")

        # --- Prepare context and prompt ---
        self.history.append({"role": "user", "content": message})
        context = "\n".join(f"{h['role']}: {h['content']}" for h in self.history[-6:])

        # 🎯 Prompt Instruction: Simple, clear instruction for the model to handle multilingual reply.
        prompt = (
            f"You are **Atlast Travel Assistant** — a helpful, polite AI specializing in **global travel**.\n"
            f"**STRICTLY** analyze the user's input language and respond entirely in that same language.\n"
            f"If the input is short or ambiguous (like 'mahad' or a single word), treat it as an English greeting or English travel query.\n"
            f"If the question is about travel, give detailed and polite suggestions for destinations worldwide.\n"
            f"Context:\n{context}\n\nUser: {message}"
        )

        # --- Generate response ---
        try:
            response = self.model.generate_content(prompt)
            reply = getattr(response, "text", None) or "Sorry, I couldn’t generate a reply."

            self.history.append({"role": "assistant", "content": reply})
            return reply.strip()

        except Exception as e:
            # Catching and reporting the API error is crucial for debugging
            print(f"Gemini API error: {e}")
            return "⚠️ Sorry, I encountered an issue with the Gemini API. Please try again later."