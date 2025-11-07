import os
import requests
from dotenv import load_dotenv
import google.generativeai as genai
# FIXED: Importing APIError using its specific internal file path (_error), 
# which is the most reliable way to prevent top-level ImportErrors during deployment.
from google.generativeai._error import APIError 

# Load environment variables from a .env file (for local testing only)
load_dotenv()

# --- Configuration ---
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    # This check ensures that if the key is missing in the production environment, 
    # the failure happens early and clearly.
    raise ValueError("GOOGLE_API_KEY environment variable not found. Please set it in your Render dashboard.")
    
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
        Detects the language of the input text using external translation services.
        It returns a simplified language code ('hi', 'mr', 'ta', or 'en').
        """
        # This function is kept for backward compatibility with your existing structure.
        
        # Simplified language detection logic based on your previous design
        text_lower = text.lower()
        if "namaste" in text_lower or "kahaan" in text_lower or "hai" in text_lower:
            return "hi"
        if "kute" in text_lower or "tumhi" in text_lower or "maharashtra" in text_lower:
            return "mr"
        if "nandri" in text_lower or "enna" in text_lower or "vandhar" in text_lower:
            return "ta"
        
        # Fallback to external services (if the simple check fails)
        for base in SERVERS:
            try:
                # Attempt to use the detect endpoint of the external service
                url = f"{base}/detect"
                # Using requests.post for LibreTranslate-compatible servers
                r = requests.post(url, json={"q": text[:100]}, timeout=4) 
                
                # Check for successful response
                if r.status_code == 200:
                    detections = r.json()
                    if detections and len(detections) > 0:
                        detected_lang = detections[0].get('lang', 'en')
                        if detected_lang.startswith('en'): return 'en'
                        if detected_lang.startswith(('hi', 'dev')): return 'hi'
                        if detected_lang.startswith('mr'): return 'mr'
                        if detected_lang.startswith('ta'): return 'ta'
                        # Default to Hindi for other Indian languages, or English
                        return 'hi' if detected_lang in ['gu', 'bn', 'te'] else 'en'

            except Exception:
                # Try the next server if this one fails
                continue
        
        return "en" # default to English if all detection fails

    def _translate(self, text, target):
        """Translates text from English to the target language (or vice-versa) using external services."""
        
        source_lang = "en"
        target_lang = target
        
        # Determine the source language based on the target
        if target == 'en':
            source_lang = self._detect(text) # Re-detect the language if we are translating back to EN
        else:
            source_lang = 'en' # If target is NOT en, we assume the source is 'en'
            
        if source_lang == target_lang:
             return text # No translation needed
        
        for base in SERVERS:
            try:
                # Use LibreTranslate-compatible API
                r = requests.post(f"{base}/translate", 
                                  json={"q": text, "source": source_lang, "target": target_lang, "format": "text"}, 
                                  timeout=6)
                
                if r.status_code == 200:
                    return r.json().get("translatedText", text)
            except Exception:
                continue
        
        # Fallback: if external services fail, return original text
        return text

    def ask(self, message, target_lang=None):
        """
        Processes a user query in any language, translates it, gets a Gemini
        response, and translates the final reply back into the user's language.
        """
        # 1. Detect language of the user's message
        detected_lang = self._detect(message)
        
        # 2. Normalize the language code for the target reply (to 'hi', 'mr', 'ta', or 'en')
        target_lang = target_lang or detected_lang # Use provided lang if available, else detected
        
        if target_lang.startswith(('hi', 'dev')): target_lang = 'hi'
        elif target_lang.startswith('mr'): target_lang = 'mr'
        elif target_lang.startswith('ta'): target_lang = 'ta'
        else: target_lang = 'en' # Default for English/unknown

        # 3. Translate the user message to English for Gemini
        msg_en = self._translate(message, "en") if target_lang != "en" else message
        
        # 4. Append English user message to history
        self.history.append({"role": "user", "content": msg_en})

        # 5. Prepare the system prompt and conversation context
        # Use a maximum of 8 turns for context
        context = "\n".join(f"{h['role']}: {h['content']}" for h in self.history[-8:])
        
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
            
        except APIError as e: # This is now APIError from the direct internal import
            # Handle specific API errors (e.g., authentication, rate limit)
            print(f"Gemini API Error: {e}")
            # Reraise the exception so app.py can catch and handle it gracefully
            raise
        except Exception as e:
            # Handle general exceptions
            print(f"An unexpected error occurred: {e}")
            raise