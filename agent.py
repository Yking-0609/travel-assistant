import os
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.errors import APIError 

# Load environment variables from a .env file (for API Key)
load_dotenv()

# --- Configuration ---
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    # If the environment variable is not set, raise an error immediately.
    raise ValueError("GOOGLE_API_KEY environment variable not found. Please set it.")
    
genai.configure(api_key=API_KEY)

# Note: External translation/detection logic has been removed. 
# We now rely solely on Gemini's superior multilingual capabilities.

class GeminiAssistant:
    def __init__(self):
        # Use a reliable model for chat and language tasks
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        # History is now stored in the original user/model languages
        self.history = []

    def greet(self):
        """Generates a universal multilingual greeting message."""
        # A simple, globally welcoming greeting
        return "Hello! I am your Global Travel Assistant. How can I help you plan your next adventure? (Puedes escribirme en tu idioma / Write to me in your language!)"

    def ask(self, message):
        """
        Processes a user message by detecting the language and responding in kind.
        This function leverages Gemini's built-in multilingual support.
        """
        
        # 1. Update history with the raw user message in its original language
        self.history.append({"role": "user", "content": message})
        
        # 2. Prepare conversation context
        # Keeping history in original languages allows Gemini to handle the multilingual flow naturally.
        context = "\n".join(f"{h['role']}: {h['content']}" for h in self.history[-8:])
        
        # 3. Create a powerful, universal system instruction
        system_instruction = (
            "You are a Global Travel Assistant. Your purpose is to provide helpful, "
            "detailed travel information and advice for any location requested worldwide. "
            "You MUST detect the user's input language and respond fluently, politely, "
            "and entirely in that same language. Use bullet points for lists and always be encouraging. "
        )
        
        # 4. Construct the final prompt
        prompt = (
            f"{system_instruction}\n\n"
            f"Conversation Context:\n{context}\n\n"
            f"User Query: {message}"
        )
        
        try:
            # 5. Get reply from Gemini
            response = self.model.generate_content(prompt)
            reply_text = response.text
            
            # 6. Update history with the model's reply (in its original language)
            self.history.append({"role": "model", "content": reply_text})
            
            return reply_text
            
        except APIError as e:
            print(f"Gemini API Error: {e}")
            raise
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            raise