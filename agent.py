import os
import requests
from dotenv import load_dotenv
import google.generativeai as genai
# ✅ FIX: APIError is now imported directly from the main package
from google.generativeai import APIError 

# Load environment variables (GOOGLE_API_KEY) from a .env file locally
load_dotenv()

# --- Configuration ---
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    # Essential for preventing silent failures
    raise ValueError("GOOGLE_API_KEY environment variable not found. Please set it.")
    
genai.configure(api_key=API_KEY)

# External translation services for language detection and back-translation
SERVERS = [
    "https://translate.argosopentech.com",
    "https://libretranslate.de",
    "https://translate.terraprint.co",
    "https://api.mymemory.translated.net"
]

class GeminiAssistant:
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        self.history = []

    def greet(self):
        """Generates a multilingual greeting message."""
        return "Namaste! Where do you want to go? / कुठे जायचे?"

    def _detect(self, text):
        """
        Detects the language of the input text using external services.
        Falls back to 'en' if all servers fail.
        """
        for base in SERVERS:
            try:
                # Use mymemory's specific detection endpoint logic
                if "mymemory" in base:
                    url = f"{base}/api/get"
                    # Only send a small portion of text for faster detection
                    r = requests.get(url, params={"q": text[:50]}, timeout=4)
                    r.raise_for_status()
                    return r.json()["responseData"]["detectedLanguage"]
                # Use standard LibreTranslate API
                else:
                    url = f"{base}/detect"
                    r = requests.post(url, json={"q": text}, timeout=4)
                    r.raise_for_status()
                    return r.json()[0]['language']
            except (requests.exceptions.RequestException, KeyError, IndexError, ValueError) as e:
                print(f"Warning: Language detection failed on {base}: {e}")
                continue
        return "en" # Fallback

    def _translate(self, text, target):
        """
        Translates text to a target language (source is usually inferred/English).
        """
        source = 'en' # Assuming source is English if target is not 'en'
        if target == 'en': source = self._detect(text) # If target is EN, detect source
        
        for base in SERVERS:
            try:
                if "mymemory" in base:
                    url = f"{base}/get"
                    r = requests.get(url, params={"q": text, "langpair": f"{source}|{target}"}, timeout=4)
                    r.raise_for_status()
                    return r.json()["responseData"]["translatedText"]
                else:
                    url = f"{base}/translate"
                    r = requests.post(url, json={"q": text, "source": source, "target": target, "format": "text"}, timeout=4)
                    r.raise_for_status()
                    return r.json().get("translatedText", text)
            except (requests.exceptions.RequestException, KeyError, ValueError) as e:
                print(f"Warning: Translation failed on {base}: {e}")
                continue
        return text 

    def ask(self, message):
        """
        Handles the full chat flow: detect -> translate (if needed) -> prompt Gemini -> translate reply (if needed).
        """
        # 1. Detect language
        detected_lang = self._detect(message)
        
        # 2. Standardize detected language code
        if detected_lang in ['mr', 'mar']:
            target_lang = 'mr' # Marathi
        elif detected_lang in ['hi', 'hin', 'dev']:
            target_lang = 'hi' # Hindi
        elif detected_lang in ['ta', 'tam']:
            target_lang = 'ta' # Tamil
        else:
            target_lang = 'en' # English

        # 3. Translate user message to English for better Gemini comprehension
        msg_en = self._translate(message, "en") if target_lang != "en" else message
        
        # 4. Update history with English version
        self.history.append({"role": "user", "content": msg_en})

        # Keep context concise (last 8 turns)
        context = "\n".join(f"{h['role']}: {h['content']}" for h in self.history[-8:])
        
        # 5. Create prompt: Instruct Gemini to reply ONLY in the detected language
        prompt = (
            f"You are Siddhi Travel Assistant specializing in India. "
            f"Your response MUST be ONLY in the language corresponding to the code '{target_lang.upper()}' "
            f"and must use polite, conversational language. Use bullet points for lists. "
            f"Conversation Context:\n{context}\nUser Query: {msg_en}"
        )

        try:
            # 6. Get reply from Gemini
            response = self.model.generate_content(prompt)
            reply_text = response.text
            
            # 7. Update history: Store the English translation of the reply for context consistency
            if target_lang != 'en':
                # Translate Gemini's non-English reply back to English for history
                reply_en = self._translate(reply_text, "en")
            else:
                reply_en = reply_text
                
            self.history.append({"role": "model", "content": reply_en})
            
            return reply_text
            
        except APIError as e:
            print(f"Gemini API Error (likely bad API Key or rate limit): {e}")
            raise
        except Exception as e:
            print(f"An unexpected error occurred during API call: {e}")
            raise