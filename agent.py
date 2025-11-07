import os
import requests
from dotenv import load_dotenv
import google.generativeai as genai

# --- Load environment variables ---
load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError(
        "GOOGLE_API_KEY not found. Set it in your environment variables or .env file."
    )

# Configure Gemini API
genai.configure(api_key=API_KEY)

# --- External translation servers (optional) ---
SERVERS = [
    "https://translate.argosopentech.com",
    "https://libretranslate.de",
    "https://translate.terraprint.co",
]

class GeminiAssistant:
    def __init__(self):
        # Dynamically pick a working model
        try:
            available_models = genai.list_models()
            # Pick first model that supports generate_content
            for m in available_models:
                if "generateContent" in m.get("supported_methods", []):
                    self.model_name = m["name"]
                    break
            else:
                raise ValueError("No available Gemini model supports generate_content.")
            
            self.model = genai.GenerativeModel(self.model_name)
            print(f"Using Gemini model: {self.model_name}")
            
        except Exception as e:
            raise RuntimeError(f"Error initializing Gemini model: {e}")

        self.history = []

    def greet(self):
        """Multilingual greeting."""
        return "Namaste! Where do you want to go? / कुठे जायचे?"

    # --- Language detection ---
    def _detect(self, text):
        text_lower = text.lower()
        if any(k in text_lower for k in ["namaste", "hai", "kahaan"]):
            return "hi"
        if any(k in text_lower for k in ["kute", "tumhi", "maharashtra"]):
            return "mr"
        if any(k in text_lower for k in ["nandri", "enna", "vandhar"]):
            return "ta"

        # External translation service fallback
        for base in SERVERS:
            try:
                r = requests.post(f"{base}/detect", json={"q": text[:100]}, timeout=4)
                if r.status_code == 200:
                    detections = r.json()
                    if detections:
                        lang = detections[0].get("lang", "en")
                        if lang.startswith("hi") or "dev" in lang: return "hi"
                        if lang.startswith("mr"): return "mr"
                        if lang.startswith("ta"): return "ta"
                        return "en"
            except Exception:
                continue
        return "en"

    # --- Translation helper ---
    def _translate(self, text, target):
        source = "en" if target != "en" else self._detect(text)
        if source == target:
            return text

        for base in SERVERS:
            try:
                r = requests.post(
                    f"{base}/translate",
                    json={"q": text, "source": source, "target": target, "format": "text"},
                    timeout=6,
                )
                if r.status_code == 200:
                    return r.json().get("translatedText", text)
            except Exception:
                continue
        return text

    # --- Main chat method ---
    def ask(self, message, target_lang=None):
        detected = self._detect(message)
        target_lang = target_lang or detected
        if target_lang.startswith(("hi", "dev")):
            target_lang = "hi"
        elif target_lang.startswith("mr"):
            target_lang = "mr"
        elif target_lang.startswith("ta"):
            target_lang = "ta"
        else:
            target_lang = "en"

        # Translate user message to English for Gemini
        msg_en = self._translate(message, "en") if target_lang != "en" else message
        self.history.append({"role": "user", "content": msg_en})

        # Build context
        context = "\n".join(f"{h['role']}: {h['content']}" for h in self.history[-8:])
        prompt = (
            f"You are Siddhi Travel Assistant. Provide helpful, polite travel guidance for India. "
            f"Reply ONLY in the language '{target_lang.upper()}'. Use bullet points when listing. "
            f"Conversation Context:\n{context}\nUser Query: {msg_en}"
        )

        try:
            response = self.model.generate_content(prompt)
            reply_text = getattr(response, "text", None) or "Sorry, I couldn't generate a reply."

            # Save English version in history
            reply_en = self._translate(reply_text, "en") if target_lang != "en" else reply_text
            self.history.append({"role": "model", "content": reply_en})

            return reply_text

        except Exception as e:
            print(f"Gemini API error: {e}")
            return "Sorry, there was a problem connecting to Gemini. Please try again."
