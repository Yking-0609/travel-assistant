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
        """Friendly English greeting."""
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
        """Main logic — detects if input is a place, and replies in English unless user requests otherwise."""
        if not message.strip():
            return "Please enter a message."

        message_lower = message.strip().lower()
        lang = "en"

        # --- Step 1: Basic detection ---
        try:
            detected_lang = detect(message)
        except lang_detect_exception.LangDetectException:
            detected_lang = "en"
        except Exception:
            detected_lang = "en"

        # --- Step 2: Handle explicit language requests ---
        if "in hindi" in message_lower:
            detected_lang = "hi"
        elif "in marathi" in message_lower:
            detected_lang = "mr"
        elif "in tamil" in message_lower:
            detected_lang = "ta"
        elif "in telugu" in message_lower:
            detected_lang = "te"
        elif "in bengali" in message_lower:
            detected_lang = "bn"
        elif "in kannada" in message_lower:
            detected_lang = "kn"
        elif "in malayalam" in message_lower:
            detected_lang = "ml"
        elif "in gujarati" in message_lower:
            detected_lang = "gu"
        elif "in english" in message_lower:
            detected_lang = "en"

        # --- Step 3: Override logic for short words like "Mahad" or "Nauru" ---
        if len(message.split()) == 1 and message.isalpha():
            # Force English and treat it as a destination
            detected_lang = "en"
            is_destination = True
        else:
            is_destination = False

        # --- Step 4: Somali or misclassified short input fix ---
        if detected_lang == "so" and len(message.split()) <= 2:
            detected_lang = "en"

        # --- Step 5: Override English for ASCII-only text (prevents false positives) ---
        if detected_lang != "en" and all(c.isascii() for c in message):
            detected_lang = "en"

        lang = detected_lang
        print(f"🌍 Final language selected: {lang} | Destination mode: {is_destination}")

        # --- Prepare prompt ---
        self.history.append({"role": "user", "content": message})
        context = "\n".join(f"{h['role']}: {h['content']}" for h in self.history[-6:])

        if is_destination:
            # Treat single-word input as place
            prompt = (
                f"You are **Atlast Travel Assistant**, an expert global travel guide.\n"
                f"The user provided the word '{message}'. Assume this refers to a **travel destination**, "
                f"not a person's name or greeting.\n"
                f"Describe it in a friendly, informative English tone.\n"
                f"Include location details, key attractions, history, culture, and travel tips.\n"
                f"Start by clarifying politely that you assume it's a place, e.g., "
                f"'I assume you meant the place {message} — here’s what you can explore there.'\n"
                f"Context:\n{context}\n\nUser: {message}"
            )
        else:
            # Normal conversation
            prompt = (
                f"You are **Atlast Travel Assistant**, a helpful AI travel expert.\n"
                f"Always reply in **English** unless the user explicitly asks for another language.\n"
                f"User language code: {lang}\n"
                f"Context:\n{context}\n\nUser: {message}"
            )

        # --- Step 6: Generate response ---
        try:
            response = self.model.generate_content(prompt)
            reply = getattr(response, "text", None) or "Sorry, I couldn’t generate a reply."
            self.history.append({"role": "assistant", "content": reply})
            return reply.strip()

        except Exception as e:
            print(f"Gemini API error: {e}")
            return "⚠️ Sorry, I couldn’t connect to Gemini. Please try again later."
