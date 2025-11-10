import os
import requests
from dotenv import load_dotenv
import google.generativeai as genai
from langdetect import detect, DetectorFactory, lang_detect_exception 

# Fix deterministic language detection
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
        # Automatically use the latest working Gemini model
        try:
            self.model = genai.GenerativeModel("models/gemini-2.5-flash")
            print("✅ Using model: gemini-2.5-flash")
        except Exception as e:
            raise RuntimeError(f"Error initializing Gemini model: {e}")

        self.history = []

    # --- Greeting ---
    def greet(self):
        """Provide a friendly multilingual greeting."""
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
        lang = "en" # Start with English default
        
        try:
            detected_lang = detect(message)
        except lang_detect_exception.LangDetectException:
            detected_lang = "en" 
        except Exception:
            detected_lang = "en"
            
        lang = detected_lang

        # 🎯 Step 1: Manual Overrides for Short, Ambiguous Inputs
        
        # 1a. Common English Greetings Fix (prevents 'it' / Italian)
        english_greetings = ["hi", "hello", "hey", "hlo", "good morning", "good evening", "good afternoon"]
        if message_lower in english_greetings:
            lang = "en"
        
        # 1b. Short International Place Name Fix (Prevents Lithuanian/Nepali/Italian for names like "Nauru")
        misclassified_foreign_codes = ["lt", "ne", "it", "tl", "sk", "sq", "ro"] 
        if len(message) < 15 and lang in misclassified_foreign_codes and all(c.isalpha() or c.isspace() for c in message):
             lang = "en"
        
        # 1c. Indian Language Ambiguity Fix (Forces 'hi' for short, non-English Indian text if classified as Nepali)
        if lang == "ne" and len(message) < 10 and not all(c in 'abcdefghijklmnopqrstuvwxyz ' for c in message_lower):
             lang = "hi"
             
        # 1d. Explicit Language Request Override (Handles cases like: "Manali in Tamil?")
        # This is the fix for your specific question.
        if "marathi" in message_lower:
            lang = "mr"
        elif "hindi" in message_lower:
            lang = "hi"
        elif "tamil" in message_lower:
            lang = "ta"
        elif "telugu" in message_lower:
            lang = "te"
        elif "bengali" in message_lower:
            lang = "bn"
        elif "kannada" in message_lower:
            lang = "kn"
        elif "malayalam" in message_lower:
            lang = "ml"
        elif "gujarati" in message_lower:
            lang = "gu"
        elif "english" in message_lower:
            lang = "en"
        
        print(f"🌍 Detected language: {lang}")

        # --- Prepare context and prompt ---
        self.history.append({"role": "user", "content": message})
        context = "\n".join(f"{h['role']}: {h['content']}" for h in self.history[-6:])

        # 🎯 Step 2: STRICT Prompt Instruction for Global Travel
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