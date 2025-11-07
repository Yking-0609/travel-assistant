import os
import requests
from dotenv import load_dotenv
import google.generativeai as genai

# ✅ Load environment variables
load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable not found. Please set it in Render's dashboard.")

genai.configure(api_key=API_KEY)

# --- External translation servers (optional) ---
SERVERS = [
    "https://translate.argosopentech.com",
    "https://libretranslate.de",
    "https://translate.terraprint.co",
]

class GeminiAssistant:
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        self.history = []

    def greet(self):
        """Generate a multilingual greeting."""
        return "Namaste! Where do you want to go? / कुठे जायचे?"

    # --- Language detection ---
    def _detect(self, text):
        text_lower = text.lower()

        # Simple keyword detection (fast)
        if any(k in text_lower for k in ["namaste", "hai", "kahaan"]):
            return "hi"
        if any(k in text_lower for k in ["kute", "tumhi", "maharashtra"]):
            return "mr"
        if any(k in text_lower for k in ["nandri", "enna", "vandhar"]):
            return "ta"

        # External detection fallback
        for base in SERVERS:
            try:
                r = requests.post(f"{base}/detect", json={"q": text[:100]}, timeout=4)
                if r.status_code == 200:
                    detections = r.json()
                    if detections:
                        lang = detections[0].get("lang", "en")
                        if lang.startswith("hi") or "dev" in lang:
                            return "hi"
                        if lang.startswith("mr"):
                            return "mr"
                        if lang.startswith("ta"):
                            return "ta"
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
        return text  # fallback

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

        # Translate to English for Gemini
        msg_en = self._translate(message, "en") if target_lang != "en" else message
        self.history.append({"role": "user", "content": msg_en})

        # Build conversation context
        context = "\n".join(f"{h['role']}: {h['content']}" for h in self.history[-8:])
        prompt = (
            f"You are Siddhi Travel Assistant. Provide helpful, polite travel guidance for India. "
            f"Reply ONLY in the language '{target_lang.upper()}'. Use bullet points when listing. "
            f"Conversation Context:\n{context}\nUser Query: {msg_en}"
        )

        try:
            response = self.model.generate_content(prompt)
            reply_text = response.text or "Sorry, I couldn’t generate a reply."

            # Save English version in history for context continuity
            reply_en = self._translate(reply_text, "en") if target_lang != "en" else reply_text
            self.history.append({"role": "model", "content": reply_en})

            return reply_text

        except Exception as e:
            print(f"Gemini API error: {e}")
            return "Sorry, there was a problem connecting to Gemini. Please try again."
