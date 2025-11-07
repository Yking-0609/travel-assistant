import os
import requests
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.errors import APIError # Import specific API error

# Load environment variables from a .env file (for API Key)
load_dotenv()

# --- Configuration ---
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    # If the environment variable is not set, raise an error immediately.
    raise ValueError("GOOGLE_API_KEY environment variable not found. Please set it.")
    
genai.configure(api_key=API_KEY)

# 5 BULLETPROOF SERVERS for external translation/detection (as in your original file)
SERVERS = [
    "https://translate.argosopentech.com",
    "https://libretranslate.de",
    "https://translate.terraprint.co",
    # Note: Using external translation services can be unreliable and slow.
    # For a fully robust solution, it's often better to ask Gemini to translate/detect directly.
]

class GeminiAssistant:
    def __init__(self):
        # Use a reliable model for chat and language tasks
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
                if "mymemory" in base: # Your original code seemed to have a check for this, keeping it for compatibility
                    url = "https://mymemory.translated.net/api/get"
                    r = requests.get(url, params={"q": text[:50]}, timeout=4)
                    r.raise_for_status()
                    return r.json()["responseData"]["detectedLanguage"]
                else:
                    url = f"{base}/detect"
                    r = requests.post(url, json={"q": text}, timeout=4)
                    r.raise_for_status()
                    # Expects a list of detections, taking the first one
                    return r.json()[0]['language']
            except (requests.exceptions.RequestException, KeyError, IndexError, ValueError) as e:
                print(f"Warning: Language detection failed on {base}: {e}")
                continue
        # If all external services fail, assume English
        return "en"

    def _translate(self, text, target):
        """
        Translates text to a target language using external services.
        Falls back to the original text if all servers fail.
        """
        for base in SERVERS:
            try:
                # Assuming all non-mymemory servers support generic translate endpoint
                if "mymemory" in base:
                    r = requests.get(f"https://api.mymemory.translated.net/get", params={"q": text, "langpair": f"en|{target}"}, timeout=4)
                    r.raise_for_status()
                    return r.json()["responseData"]["translatedText"]
                else:
                    r = requests.post(f"{base}/translate", json={"q": text, "source": "en", "target": target, "format": "text"}, timeout=4)
                    r.raise_for_status()
                    return r.json().get("translatedText", text)
            except (requests.exceptions.RequestException, KeyError, ValueError) as e:
                print(f"Warning: Translation failed on {base}: {e}")
                continue
        return text # Return original text if translation fails

    def ask(self, message):
        """
        Handles the conversation: detects language, translates to English for prompt,
        gets Gemini reply, and translates reply back to the user's language.
        """
        # 1. Detect language (returns two-letter code, e.g., 'en', 'hi', 'mr', 'ta')
        detected_lang = self._detect(message)
        
        # 2. Standardize detected language for target use
        # This mapping is crucial for your specific Indian language support
        if detected_lang in ['mr', 'mar']:
            target_lang = 'mr'
        elif detected_lang in ['hi', 'hin', 'dev']:
            target_lang = 'hi'
        elif detected_lang in ['ta', 'tam']:
            target_lang = 'ta'
        else:
            # Default to English (en) for prompt if detection is not Hindi/Marathi/Tamil
            target_lang = 'en' 

        # 3. Translate user message to English (unless it's already English)
        msg_en = self._translate(message, "en") if target_lang != "en" else message
        
        # 4. Prepare conversation history for context
        self.history.append({"role": "user", "content": msg_en})

        # Keep context concise (last 8 turns)
        context = "\n".join(f"{h['role']}: {h['content']}" for h in self.history[-8:])
        
        # 5. Create prompt: Instruct Gemini to reply ONLY in the detected language
        # We instruct Gemini to use the target_lang code for the reply.
        prompt = (
            f"You are Siddhi Travel Assistant. Your purpose is to provide travel information for India. "
            f"Reply ONLY in the language corresponding to the code '{target_lang.upper()}'. "
            f"Use polite language and bullet points for lists. "
            f"Conversation Context:\n{context}\nUser Query: {msg_en}"
        )

        try:
            # 6. Get reply from Gemini
            response = self.model.generate_content(prompt)
            reply_text = response.text
            
            # 7. Update history with English version of the reply (for context persistence)
            # Since the prompt asked Gemini to reply in the target language, 
            # we must translate the reply back to English for the history if it's not 'en'
            if target_lang != 'en':
                 # Using the same translation function but now translating the reply back to English
                reply_en = self._translate(reply_text, "en")
            else:
                reply_en = reply_text
                
            self.history.append({"role": "model", "content": reply_en})
            
            return reply_text
            
        except APIError as e:
            # Handle specific API errors (e.g., authentication, rate limit)
            print(f"Gemini API Error: {e}")
            raise
        except Exception as e:
            # Handle general exceptions
            print(f"An unexpected error occurred: {e}")
            raise