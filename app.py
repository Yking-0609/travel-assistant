from flask import Flask, request, jsonify, send_from_directory, make_response, redirect
from flask_cors import CORS, cross_origin
from agent import GeminiAssistant
from database import TravelDatabase
import os

# --- Initialize Flask app ---
app = Flask(__name__)

# ✅ Allow all origins and methods (you can restrict later)
CORS(app, resources={r"/*": {"origins": "*"}})

# --- Initialize Gemini assistant and database ---
assistant = GeminiAssistant()
db = TravelDatabase()

# --- Routes ---

@app.route("/index")
def index():
    """Serve the chat HTML page"""
    return send_from_directory(".", "index.html")


@app.route("/")
@cross_origin()  # 👈 Explicit CORS for greeting
def home():
    """Default greeting route"""
    try:
        message = assistant.greet()
        response = make_response(jsonify({"message": message}))
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
    except Exception as e:
        print(f"Greeting error: {e}")
        return jsonify({"message": "Hello! How can I assist you with travel today?"})


@app.route("/chat", methods=["POST"])
@cross_origin()  # 👈 Explicit CORS for chat
def chat():
    """Chat endpoint"""
    data = request.get_json() or {}
    user_text = data.get("message", "").strip()

    if not user_text:
        return jsonify({"response": "Please type something."}), 400

    try:
        reply = assistant.ask(user_text)
    except Exception as e:
        print(f"Assistant error: {e}")
        reply = "Sorry, there was an issue generating a response."

    # Save to database safely
    try:
        db.save_search(user_text, reply)
    except Exception as e:
        print(f"Database error: {e}")

    response = make_response(jsonify({"response": reply}))
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


@app.route("/history", methods=["GET"])
@cross_origin()
def history():
    """Return all stored user queries and bot replies"""
    try:
        data = db.get_all_searches()
        return jsonify(data)
    except Exception as e:
        print(f"History fetch error: {e}")
        return jsonify({"error": str(e)}), 500


# --- Redirect base to /index for user convenience ---
@app.route("/home")
def redirect_home():
    return redirect("/index")


# --- Render-compatible entry point ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
