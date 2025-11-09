from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from agent import GeminiAssistant
from database import TravelDatabase
import os

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

# --- Initialize Gemini assistant and database ---
try:
    assistant = GeminiAssistant()
except Exception as e:
    print(f"FATAL ERROR: {e}")
    exit(1)

db = TravelDatabase()

# ✅ Serve index.html on root
@app.route("/")
def serve_index():
    return send_from_directory(".", "index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    user_text = data.get("message", "").strip()

    if not user_text:
        return jsonify({"response": "Please type something."}), 400

    try:
        reply = assistant.ask(user_text)
    except Exception as e:
        print(f"Assistant error: {e}")
        reply = "Sorry, there was an issue generating a response. Please try again later."

    try:
        db.save_search(user_text, reply)
    except Exception as e:
        print(f"Database error: {e}")

    return jsonify({"response": reply})

@app.route("/history", methods=["GET"])
def history():
    try:
        data = db.get_all_searches()
        return jsonify(data)
    except Exception as e:
        print(f"History fetch error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
