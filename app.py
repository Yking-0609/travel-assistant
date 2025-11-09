from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from agent import GeminiAssistant
from database import TravelDatabase  # Make sure this exists
import os

# --- Initialize Flask app ---
app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

# --- Initialize Gemini assistant and database ---
try:
    assistant = GeminiAssistant()
except Exception as e:
    print(f"FATAL ERROR: {e}")
    exit(1)

try:
    db = TravelDatabase()
except Exception as e:
    print(f"Database initialization error: {e}")
    db = None  # Safe fallback so app runs without DB

# --- Routes ---

@app.route("/")
def serve_index():
    """Serve the frontend HTML file."""
    return send_from_directory(".", "index.html")

@app.route("/greet")
def greet():
    """Return multilingual greeting from Gemini assistant."""
    try:
        message = assistant.greet()
        return jsonify({"message": message})
    except Exception as e:
        print(f"Greeting error: {e}")
        return jsonify({"message": "Hello! How can I assist you with travel today?"})

@app.route("/chat", methods=["POST"])
def chat():
    """Chat endpoint with automatic language detection."""
    data = request.get_json() or {}
    user_text = data.get("message", "").strip()

    if not user_text:
        return jsonify({"response": "Please type something."}), 400

    try:
        reply = assistant.ask(user_text)
    except Exception as e:
        print(f"Assistant error: {e}")
        reply = "Sorry, there was a problem connecting to Gemini. Please try again."

    # Save conversation to DB if available
    if db:
        try:
            db.save_search(user_text, reply)
        except Exception as e:
            print(f"Database save error: {e}")

    return jsonify({"response": reply})

@app.route("/history", methods=["GET"])
def history():
    """Return chat history from DB."""
    if not db:
        return jsonify({"error": "Database not configured."}), 500
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
