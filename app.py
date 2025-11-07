# app.py
from flask import Flask, request, jsonify, send_from_directory, redirect
from flask_cors import CORS
from agent import GeminiAssistant
from database import TravelDatabase
import os

app = Flask(__name__)
CORS(app)

assistant = GeminiAssistant()
db = TravelDatabase()

@app.route("/index")
def index():
    return send_from_directory(".", "index.html")

@app.route("/")
def home():
    return jsonify({"message": assistant.greet()})

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    user_msg = data.get("message", "").strip()
    if not user_msg:
        return jsonify({"response": "Please type something."}), 400

    reply = assistant.ask(user_msg)  # Auto-detects language
    try:
        db.save_search(user_msg, reply)
    except:
        pass
    return jsonify({"response": reply})

@app.route("/history")
def history():
    return jsonify(db.get_all_searches())

@app.route("/home")
def redirect_home():
    return redirect("/index")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))