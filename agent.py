# agent.py
import os
import requests
from dotenv import load_dotenv
import google.generativeai as genai

# -------------------------------------------------------
# Load .env
# -------------------------------------------------------
load_dotenv()
GEMINI_KEY = os.getenv("GOOGLE_API_KEY")
if not GEMINI_KEY:
    raise ValueError("Add GOOGLE_API_KEY=your_key in .env")

genai.configure(api_key=GEMINI_KEY)

# FREE translation servers (auto-fallback)
FREE_SERVERS = [
    "https://libretranslate.de/translate",
    "https://translate.terraprint.co/translate",
    "https://translate.argosopentech.com/translate"
]

# -------------------------------------------------------
# Gemini Travel Assistant (Multilingual + Bulletproof)
# -------------------------------------------------------
class GeminiAssistant:
    def __init__(self, model_name="gemini-1.5-flash"):
        self.model = genai.GenerativeModel(model_name)
        self.conversation = []

    def greet(self) -> str:
        return "Hello! I'm your travel assistant by Atlast Tours & Travels. Where would you like to go?"

    def _translate(self, text: str, target: str = "en", source: str = "auto") -> str:
        if not text.strip():
            return text
        payload = {"q": text, "source": source, "target": target, "format": "text"}
        for url in FREE_SERVERS:
            try:
                r = requests.post(url, json=payload, timeout=6)
                if r.status_code == 200:
                    return r.json()["translatedText"]
            except:
                continue
        print("All translation servers down – returning original text")
        return text  # ultimate fallback

    def ask(self, user_message: str, lang: str = "en") -> str:
        try:
            # 1. User → English
            user_en = self._translate(user_message, "en", lang) if lang != "en" else user_message

            # 2. Chat with Gemini
            self.conversation.append({"role": "user", "content": user_en})
            context = "\n".join(
                f"{m['role'].capitalize()}: {m['content']}"
                for m in self.conversation[-12:]
            )
            prompt = (
                "You are a fun, expert travel assistant for Atlast Tours.\n"
                "Reply in short bullet points. Be exciting!\n\n" + context
            )
            reply_en = self.model.generate_content(prompt).text.strip()

            # 3. Save
            self.conversation.append({"role": "assistant", "content": reply_en})

            # 4. English → User language
            reply = self._translate(reply_en, lang) if lang != "en" else reply_en

            return reply

        except Exception as e:
            print(f"Error: {e}")
            return "I'm planning your perfect trip! Try again in 10 sec"