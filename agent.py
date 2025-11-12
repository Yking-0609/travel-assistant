import os
from dotenv import load_dotenv
import google.generativeai as genai

# --- Load environment variables ---
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError("GOOGLE_API_KEY not found. Set it in your environment variables or .env file.")

# --- Configure Gemini API ---
genai.configure(api_key=API_KEY)

# --- Removed: External translation servers (SERVERS list) ---

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
        return "👋 Hello! Welcome to **Atlast Travel Assistant**. Where would you like to go today? (We cover destinations worldwide!)"

    # --- Removed: _translate method ---

    def ask(self, message):
        """Main logic — generates an English response for travel inquiries."""
        if not message.strip():
            return "Please enter a message."

        # Hardcode language to English
        lang = "en"
        
        print(f"🌍 Reply language set to: {lang}")

        # --- Prepare context and prompt ---
        self.history.append({"role": "user", "content": message})
        context = "\n".join(f"{h['role']}: {h['content']}" for h in self.history[-6:])

        # 🎯 Prompt Instruction for Global Travel and Strict English Reply
        prompt = (
            f"You are **Atlast Travel Assistant** — a helpful, polite AI specializing in **global travel**.\n"
            f"You **MUST** reply in **English**, regardless of the user's input language.\n"
            f"If the question is about travel, give detailed and polite suggestions for destinations worldwide.\n"
            f"Context:\n{context}\n\nUser: {message}"
        )

        # --- Generate response ---
        try:
            response = self.model.generate_content(prompt)
            reply = getattr(response, "text", None) or "Sorry, I couldn’t generate a reply."

            self.history.append({"role": "assistant", "content": reply})
            return reply.strip()

        except Exception as e:
            print(f"Gemini API error: {e}")
            return "⚠️ Sorry, I couldn’t connect to Gemini. Please try again later."