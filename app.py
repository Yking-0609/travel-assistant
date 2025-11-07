from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from agent import GeminiAssistant
from database import TravelDatabase  # Make sure this exists
import os

# --- Initialize Flask app ---
app = Flask(__name__)
CORS(app)  # Allow all origins by default

# --- Initialize Gemini assistant and database ---
try:
    assistant = GeminiAssistant()
except ValueError as e:
    print(f"FATAL ERROR: {e}")
    exit(1)

db = TravelDatabase()  # Initialize your database handler

# --- Routes ---

@app.route("/index")
def index():
    """Serve chat HTML page (for testing)."""
    return send_from_directory(".", "index.html")

@app.route("/")
def home():
    """Default greeting route."""
    try:
        message = assistant.greet()
        return jsonify({"message": message})
    except Exception as e:
        print(f"Greeting error: {e}")
        return jsonify({"message": "Hello! How can I assist you with travel today?"})

@app.route("/chat", methods=["POST"])
def chat():
    """Chat endpoint with auto-detect language support."""
    data = request.get_json() or {}
    user_text = data.get("message", "").strip()

    if not user_text:
        return jsonify({"response": "Please type something."}), 400

    try:
        reply = assistant.ask(user_text)
    except Exception as e:
        print(f"Assistant error: {e}")
        reply = "Sorry, there was an issue generating a response. Please try again later."

    # Save chat history in database
    try:
        db.save_search(user_text, reply)
    except Exception as e:
        print(f"Database error: {e}")

    return jsonify({"response": reply})

@app.route("/history", methods=["GET"])
def history():
    """Return stored user queries and bot replies."""
    try:
        data = db.get_all_searches()
        return jsonify(data)
    except Exception as e:
        print(f"History fetch error: {e}")
        return jsonify({"error": str(e)}), 500

# --- Run the App ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
