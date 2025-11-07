# agent.py
import os
import requests
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
GEMINI_KEY = os.getenv("GOOGLE_API_KEY")
if not GEMINI_KEY:
    raise ValueError("Add GOOGLE_API_KEY in .env")

genai.configure(api_key=GEMINI_KEY)

TRANSLATE_SERVERS = [
    "https://libretranslate.de/translate",
    "https://translate.terraprint.co/translate",
    "https://translate.argosopentech.com/translate"
]

class GeminiAssistant:
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        self.history = []

    def greet(self):
        return "Hello! I'm your travel assistant by Atlast Tours & Travels. Where would you like to go?"

    def _translate(self, text, to_lang="en", from_lang="auto"):
        if not text.strip(): return text
        payload = {"q": text, "source": from_lang, "target": to_lang, "format": "text"}
        for url in TRANSLATE_SERVERS:
            try:
                r = requests.post(url, json=payload, timeout=5)
                if r.status_code == 200:
                    return r.json()["translatedText"]
            except:
                continue
        return text

    def ask(self, message, lang="en"):
        try:
            msg_en = self._translate(message, "en", lang) if lang != "en" else message
            self.history.append({"role": "user", "content": msg_en})
            context = "\n".join(f"{h['role']}: {h['content']}" for h in self.history[-10:])
            prompt = f"You are a fun travel assistant. Reply in short bullet points.\n\n{context}"
            reply_en = self.model.generate_content(prompt).text.strip()
            self.history.append({"role": "assistant", "content": reply_en})
            return self._translate(reply_en, lang) if lang != "en" else reply_en
        except:
            return "I'm planning your trip! Try again"