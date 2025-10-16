from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from agent import GeminiAssistant
from database import TravelDatabase
import os

# --- Initialize Flask app ---
app = Flask(__name__)
CORS(app)

# --- Initialize Gemini assistant and database ---
assistant = GeminiAssistant()
db = TravelDatabase()


# --- Routes ---

@app.route("/index")
def index():
    """Serve the chat HTML page"""
    return send_from_directory(".", "index.html")


@app.route("/")
def home():
    """Default greeting route"""
    return jsonify({"message": assistant.greet()})


@app.route("/chat", methods=["POST"])
def chat():
    """Chat endpoint"""
    data = request.get_json() or {}
    user_text = data.get("message", "").strip()

    if not user_text:
        return jsonify({"response": "Please type something."}), 400

    # Get AI reply
    reply = assistant.ask(user_text)

    # Save to database
    try:
        db.save_search(user_text, reply)
    except Exception as e:
        print(f"Database error: {e}")

    return jsonify({"response": reply})


# --- Render-compatible entry point ---
if __name__ == "__main__":
    # IMPORTANT: use the PORT Render provides
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
