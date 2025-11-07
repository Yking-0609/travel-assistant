from flask import Flask, request, jsonify, send_from_directory, make_response
from flask_cors import CORS
from agent import GeminiAssistant
from database import TravelDatabase
import os

# --- Initialize Flask app ---
app = Flask(__name__)

# ✅ Allow all origins and methods
CORS(app, resources={r"/*": {"origins": "*"}})

# --- Initialize Gemini assistant and database ---
try:
    assistant = GeminiAssistant()
except ValueError as e:
    print(f"❌ FATAL ERROR: {e}")
    exit(1)
except Exception as e:
    print(f"❌ Unexpected initialization error: {e}")
    exit(1)

try:
    db = TravelDatabase()
except Exception as e:
    print(f"⚠️ Database initialization error: {e}")
    db = None  # Continue without DB to avoid full crash

# --- Routes ---

@app.route("/")
def home():
    """Default greeting route"""
    try:
        message = assistant.greet()
        return jsonify({"message": message})
    except Exception as e:
        print(f"⚠️ Greeting error: {e}")
        return jsonify({"message": "Hello! How can I assist you with travel today? (Fallback mode)"}), 200


@app.route("/index")
def index():
    """Serve the chat HTML page (for manual testing)"""
    return send_from_directory(".", "index.html")


@app.route("/chat", methods=["POST"])
def chat():
    """Main multilingual chat endpoint"""
    try:
        data = request.get_json(force=True)
        user_text = (data.get("message") or "").strip()

        if not user_text:
            return jsonify({"response": "Please type something."}), 400

        reply = assistant.ask(user_text)

        # Save to database safely (if available)
        if db:
            try:
                db.save_search(user_text, reply)
            except Exception as e:
                print(f"⚠️ Database save error: {e}")

        return jsonify({"response": reply})

    except Exception as e:
        print(f"❌ Chat error: {e}")
        return jsonify({"response": "Sorry, there was a server issue. Please try again later."}), 500


@app.route("/history", methods=["GET"])
def history():
    """Return stored user queries and replies"""
    if not db:
        return jsonify({"error": "Database not initialized."}), 503

    try:
        return jsonify(db.get_all_searches())
    except Exception as e:
        print(f"⚠️ History fetch error: {e}")
        return jsonify({"error": str(e)}), 500


# --- Run the App ---
if __name__ == "__main__":
    # Render provides the PORT environment variable automatically
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Starting Flask app on port {port} ...")
    app.run(host="0.0.0.0", port=port, debug=False)
