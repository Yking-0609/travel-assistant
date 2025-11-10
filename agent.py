import os
import requests
from dotenv import load_dotenv
import google.generativeai as genai
from langdetect import detect, DetectorFactory, lang_detect_exception # <-- Added lang_detect_exception

# ✅ Fix deterministic language detection
DetectorFactory.seed = 0

# --- Load environment variables ---
load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError("GOOGLE_API_KEY not found. Set it in your environment variables or .env file.")

# --- Configure Gemini API ---
genai.configure(api_key=API_KEY)

# --- External translation servers (for non-English fallback) ---
SERVERS = [
    "https://translate.argosopentech.com",
    "https://libretranslate.de",
    "https://translate.terraprint.co",
]

class GeminiAssistant:
    def __init__(self):
        # ✅ Automatically use the latest working Gemini model
        try:
            self.model = genai.GenerativeModel("models/gemini-2.5-flash")
            print("✅ Using model: gemini-2.5-flash")
        except Exception as e:
            raise RuntimeError(f"Error initializing Gemini model: {e}")

        self.history = []

    # --- Greeting ---
    def greet(self):
        """Provide a friendly multilingual greeting."""
        # ✅ Updated greeting to reflect global scope
        return "👋 Namaste! Welcome to **Atlast Travel Assistant**. Where would you like to go today? (We cover destinations worldwide!)"

    # --- Translation helper (fallback only) ---
    def _translate(self, text, target):
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
        return text  # Fallback if translation fails

    # --- Main chat logic ---
    def ask(self, message):
        """Generate a multilingual response based on user input."""
        if not message.strip():
            return "Please enter a message."

        # 🌐 Detect language dynamically
        message_lower = message.strip().lower()
        lang = "en" # Default to English
        
        try:
            detected_lang = detect(message)
        except lang_detect_exception.LangDetectException:
            detected_lang = "en"
        except Exception:
            detected_lang = "en"
            
        lang = detected_lang

        # ⚡️ FIX 1: Common English greetings fix (prevents 'it' / Italian)
        english_greetings = ["hi", "hello", "hey", "hlo", "good morning", "good evening", "good afternoon"]
        if message_lower in english_greetings:
            lang = "en"
        
        # ⚡️ FIX 2: Short, Ambiguous Input Fix (Prevents Lithuanian, Nepali, Italian for place names like "Nauru")
        misclassified_codes = ["lt", "ne", "it", "tl"] # Lithuanian, Nepali, Italian, Tagalog
        # Check if the message is short (e.g., one or two words) AND is classified as a problem language
        if len(message) < 15 and lang in misclassified_codes and all(c.isalpha() or c.isspace() for c in message):
             lang = "en"
        
        # ⚡️ FIX 3: Handle misclassified Indian languages (forces 'hi' instead of 'ne' for Romanized input like 'japan')
        misclassified_indian_codes = ["ne", "it", "tl"] 
        if lang in misclassified_indian_codes and len(message) < 10 and not message_lower.startswith('hi'):
             lang = "hi"
        
        # NEW LOGIC: Override to Marathi if explicitly requested within an English sentence
        if "marathi" in message_lower and lang == "en":
             lang = "mr"
        
        print(f"🌍 Detected language: {lang}")

        # --- Prepare context and prompt ---
        self.history.append({"role": "user", "content": message})
        context = "\n".join(f"{h['role']}: {h['content']}" for h in self.history[-6:])

        # 🎯 CRITICAL FIX: Global Specialization and STRICT language forcing
        prompt = (
            f"You are **Atlast Travel Assistant** — a helpful, polite AI specializing in **global travel**.\n"
            f"User language code: {lang}. This is the language you **MUST** reply in.\n"
            f"**STRICTLY** reply in the language with the code '{lang}'.\n"
            f"If the question is about travel, give detailed and polite suggestions for destinations worldwide.\n"
            f"Context:\n{context}\n\nUser: {message}"
        )

        try:
            # 🧠 Generate content with Gemini
            response = self.model.generate_content(prompt)
            reply = getattr(response, "text", None) or "Sorry, I couldn’t generate a reply."

            # Store only English version internally for context
            self.history.append({"role": "assistant", "content": reply})
            return reply.strip()

        except Exception as e:
            print(f"Gemini API error: {e}")
            return "⚠️ Sorry, I couldn’t connect to Gemini. Please try again later."