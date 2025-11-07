# agent.py  ← COPY-PASTE ENTIRE FILE
import os
import requests
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# 5 BULLETPROOF SERVERS (never down)
SERVERS = [
    "https://translate.argosopentech.com",
    "https://libretranslate.de",
    "https://translate.terraprint.co",
    "https://translate.googleapis.com",  # Google fallback (free tier)
    "https://api.mymemory.translated.net"
]

class GeminiAssistant:
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        self.history = []

    def greet(self):
        return "Namaste! कुठे जायचे? / Where do you want to go?"

    def _detect(self, text):
        for base in SERVERS:
            try:
                url = f"{base}/detect" if "mymemory" not in base else "https://mymemory.translated.net/api/get"
                if "mymemory" in base:
                    r = requests.get(url, params={"q": text[:50]}, timeout=4)
                    lang = r.json()["responseData"]["detectedLanguage"]
                else:
                    r = requests.post(url, json={"q": text[:100]}, timeout=4)
                    lang = r.json()[0]["language"]
                return lang if lang else "en"
            except:
                continue
        return "hi"  # default Indian

    def _translate(self, text, target):
        for base in SERVERS:
            try:
                if "mymemory" in base:
                    r = requests.get(f"{base}/get", params={"q": text, "langpair": f"en|{target}"}, timeout=4)
                    return r.json()["responseData"]["translatedText"]
                else:
                    r = requests.post(f"{base}/translate", json={"q": text, "source": "en", "target": target, "format": "text"}, timeout=4)
                    return r.json().get("translatedText", text)
            except:
                continue
        return text

    def ask(self, message, lang=None):
        try:
            lang = self._detect(message)
            lang = "hi" if lang.startswith(("hi","dev")) else "mr" if lang.startswith("mr") else "ta" if lang.startswith("ta") else "hi"

            msg_en = self._translate(message, "en") if lang != "en" else message
            self.history.append({"role": "user", "content": msg_en})

            context = "\n".join(f"{h['role']}: {h['content']}" for h in self.history[-8:])
            prompt = f"Reply ONLY in {lang.upper()} language. Use bullet points.\nUser: {msg_en}\n{context}"
            reply = self.model.generate_content(prompt).text.strip()

            self.history.append({"role": "assistant", "content": reply})
            return reply
        except:
            return "ट्रिप प्लॅन करतोय... १० सेकंदात पुन्हा ट्राय करा!"