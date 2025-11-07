import os
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS, cross_origin
from dotenv import load_dotenv

# Import the corrected agent and database classes
from agent import GeminiAssistant
from database import TravelDatabase 

# Load environment variables
load_dotenv()

# --- Initialize Flask app ---
app = Flask(__name__)

# ✅ Allow all origins and methods 
CORS(app, resources={r"/*": {"origins": "*"}})

# --- Initialize Gemini assistant and database ---
assistant = None
db = None

try:
    # Initialize assistant (will raise ValueError if GOOGLE_API_KEY is missing)
    assistant = GeminiAssistant()
except ValueError as e:
    print(f"FATAL ERROR: {e}")
    # Exit with status 1 to stop deployment/run if API Key is missing
    exit(1)

try:
    # Initialize database connection. Will raise ValueError if DATABASE_URL is missing.
    db = TravelDatabase() 
except ValueError as e:
    print(f"DB Initialization Error: {e}")
    print("WARNING: Application will run without database features (history/saving).")
except Exception as e:
    print(f"DB Connection Failed: {e}")
    print("WARNING: Application will run without database features (history/saving).")


# --- Routes ---

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
        return jsonify({"message": "Hello! How can I assist you with travel today?"})


@app.route("/chat", methods=["POST"])
@cross_origin() 
def chat():
    """Chat endpoint (Relying on agent.py for Auto-Detection)"""
    data = request.get_json() or {}
    user_text = data.get("message", "").strip()
    
    # We DO NOT look for 'lang' here. Auto-detection is handled by agent.py.

    if not user_text:
        return jsonify({"response": "Please type something."}), 400

    reply = "Sorry, the assistant is currently unavailable due to an internal error."
    try:
        # Pass only the user's text to the assistant
        reply = assistant.ask(user_text) 
    except Exception as e:
        # The exception is now properly caught if the API key/connection fails
        print(f"Assistant chat error: {e}")
        reply = "Sorry, the assistant encountered an error generating a response. Please check the server logs for API key or rate limit issues."

    # Save to database safely only if db object is initialized
    if db and db.conn:
        try:
            db.save_search(user_text, reply)
        except Exception as e:
            print(f"Database saving error: {e}")

    response = make_response(jsonify({"response": reply}))
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


@app.route("/history", methods=["GET"])
@cross_origin()
def history():
    """Return all stored user queries and bot replies"""
    if not db or not db.conn:
        return jsonify({"error": "Database is not connected, history unavailable."}), 503

    try:
        data = db.get_all_searches()
        return jsonify(data)
    except Exception as e:
        print(f"History fetch error: {e}")
        return jsonify({"error": str(e)}), 500


# --- Run the App ---
if __name__ == "__main__":
    app.run(debug=True)