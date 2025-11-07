from flask import Flask, request, jsonify, send_from_directory, make_response
from flask_cors import CORS, cross_origin
from agent import GeminiAssistant
from database import TravelDatabase # Assuming this file exists and works
import os

# --- Initialize Flask app ---
app = Flask(__name__)

# ✅ Allow all origins and methods 
CORS(app, resources={r"/*": {"origins": "*"}})

# --- Initialize Gemini assistant and database ---
try:
    assistant = GeminiAssistant()
except ValueError as e:
    # Handle the case where the API key is missing before running the app
    print(f"FATAL ERROR: {e}")
    exit(1)

db = TravelDatabase() # Initialize your database handler

# --- Routes ---

@app.route("/index")
def index():
    """Serve the chat HTML page (for testing directly)"""
    return send_from_directory(".", "index.html")


@app.route("/")
@cross_origin() 
def home():
    """Default greeting route"""
    try:
        # Use the assistant to get the multilingual greeting
        message = assistant.greet()
        response = make_response(jsonify({"message": message}))
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
    except Exception as e:
        print(f"Greeting error: {e}")
        return jsonify({"message": "Hello! How can I assist you with travel today? (Universal Mode)"})


@app.route("/chat", methods=["POST"])
@cross_origin() 
def chat():
    """Chat endpoint (Now relying on agent.py for Auto-Detection)"""
    data = request.get_json() or {}
    user_text = data.get("message", "").strip()
    
    # We DO NOT look for 'lang' here. Auto-detection is handled by agent.py.

    if not user_text:
        return jsonify({"response": "Please type something."}), 400

    try:
        # Pass only the user's text to the assistant
        reply = assistant.ask(user_text) 
    except Exception as e:
        # The exception is now likely an APIError from agent.py if the connection/key fails.
        print(f"Assistant error (check API Key and server logs): {e}")
        reply = "Sorry, there was an issue generating a response. Please check the backend server logs for API errors."

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


# --- Run the App ---
if __name__ == '__main__':
    # When running locally, use a port defined in the environment or default to 5000
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)