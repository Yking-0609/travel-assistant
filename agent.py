import os
import requests
from dotenv import load_dotenv
import google.generativeai as genai
from langdetect import detect, DetectorFactory, lang_detect_exception

# Deterministic results for language detection
DetectorFactory.seed = 0

# --- Load environment variables ---
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError("GOOGLE_API_KEY not found. Set it in your environment variables or .env file.")

# --- Configure Gemini API ---
genai.configure(api_key=API_KEY)

# --- External translation servers (for fallback) ---
SERVERS = [
    "https://translate.argosopentech.com",
    "https://libretranslate.de",
    "https://translate.terraprint.co",
]

class GeminiAssistant:
    def __init__(self):
        try:
            self.model = genai.GenerativeModel("models/gemini-2.5-flash")
            print("✅ Using model: gemini-2.5-flash")
        except Exception as e:
            raise RuntimeError(f"Error initializing Gemini model: {e}")

        self.history = []

    def greet(self):
        """Friendly multilingual greeting."""
        return "👋 Namaste! Welcome to **Atlast Travel Assistant**. Where would you like to go today? (We cover destinations worldwide!)"

    def _translate(self, text, target):
        """Fallback translation helper."""
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
        """Generate a multilingual response based on user input, strictly adhering to the input language."""
        if not message.strip():
            return "Please enter a message."

        # --- Step 1: Basic language detection ---
        lang = "en" # Default to English
        
        try:
            # Use 'detect' to get the single best prediction
            detected_lang = detect(message)
            lang = detected_lang
        except lang_detect_exception.LangDetectException:
            # If detection fails (e.g., short or ambiguous text), keep default 'en'.
            lang = "en" 
        except Exception:
            lang = "en"
        
        # 🎯 RULE: HARD FILTER for Somali (so) on short, ambiguous inputs
        # This prevents 'mahad' from triggering Somali while maintaining multilingual support.
        if lang == "so" and len(message.split()) <= 2:
            print("Language set to 'so' for short input. Overriding to 'en'.")
            lang = "en"
            
        print(f"🌍 Final reply language selected: {lang}")

        # --- Prepare context and prompt ---
        self.history.append({"role": "user", "content": message})
        context = "\n".join(f"{h['role']}: {h['content']}" for h in self.history[-6:])

        # 🎯 Prompt Instruction for Global Travel and Strict Multilingual Reply
        prompt = (
            f"You are **Atlast Travel Assistant** — a helpful, polite AI specializing in **global travel**.\n"
            f"The user's input language code is '{lang}'. You **MUST** reply in this language.\n"
            f"**STRICTLY** reply in the language with the code '{lang}'.\n"
            f"If the question is about travel, give detailed and polite suggestions for destinations worldwide.\n"
            f"Context:\n{context}\n\nUser: {message}"
        )

        # --- Step 2: Generate response ---
        try:
            response = self.model.generate_content(prompt)
            reply = getattr(response, "text", None) or "Sorry, I couldn’t generate a reply."

            self.history.append({"role": "assistant", "content": reply})
            return reply.strip()

        except Exception as e:
            # Check for common API errors that result in "could not generate"
            error_message = str(e).lower()
            if "safety" in error_message or "blocked" in error_message:
                 print(f"Gemini API safety error: {e}")
                 # This handles inputs like "mahad" that might be flagged as inappropriate by the model, 
                 # which prevents the generic "Sorry, I couldn’t generate a reply" error.
                 return "⚠️ I apologize, I cannot generate a response to that specific input. Please ask a travel-related question instead."
            
            print(f"Gemini API error: {e}")
            return "⚠️ Sorry, I couldn’t connect to Gemini. Please try again later."