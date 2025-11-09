from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from agent import GeminiAssistant
from database import TravelDatabase
import os

# --- Initialize Flask app ---
app = Flask(__name__)
CORS(app)

# --- Initialize Gemini assistant and database ---
try:
    assistant = GeminiAssistant()
except Exception as e:
    print(f"FATAL ERROR: {e}")
    exit(1)

db = TravelDatabase()

# --- Routes ---

@app.route("/")
def serve_home():
    """Serve the main HTML chat page."""
    return send_from_directory(".", "index.html")

@app.route("/index")
def serve_index():
    """Serve the same chat page at /index for compatibility."""
    return send_from_directory(".", "index.html")

@app.route("/greet")
def greet():
    """Return multilingual greeting message."""
    try:
        message = assistant.greet()
        return jsonify({"message": message})
    except Exception as e:
        print(f"Greeting error: {e}")
        return jsonify({"message": "Hello! How can I assist you with travel today?"})

@app.route("/chat", methods=["POST"])
def chat():
    """Main chat endpoint with auto language detection."""
    data = request.get_json() or {}
    user_text = data.get("message", "").strip()

    if not user_text:
        return jsonify({"response": "Please type something."}), 400

    try:
        reply = assistant.ask(user_text)
    except Exception as e:
        print(f"Assistant error: {e}")
        reply = "Sorry, there was an issue generating a response. Please try again later."

    # Save chat to DB
    try:
        db.save_search(user_text, reply)
    except Exception as e:
        print(f"Database error: {e}")

    return jsonify({"response": reply})

@app.route("/history", methods=["GET"])
def history():
    """Return all previous chats."""
    try:
        data = db.get_all_searches()
        return jsonify(data)
    except Exception as e:
        print(f"History fetch error: {e}")
        return jsonify({"error": str(e)}), 500

# --- Run locally or Render ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
