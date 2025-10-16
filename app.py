from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from agent import GeminiAssistant
from database import TravelDatabase  # Import the new database class

# Create Flask app
app = Flask(__name__)
CORS(app)

# Initialize Gemini assistant and database
assistant = GeminiAssistant()
db = TravelDatabase()

# Serve the chat page
@app.route("/index")
def index():
    return send_from_directory(".", "index.html")

# Greeting endpoint
@app.route("/")
def home():
    return {"message": assistant.greet()}

# Chat endpoint
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_text = data.get("message", "")

    if not user_text:
        return jsonify({"response": "Please type something."}), 400

    reply = assistant.ask(user_text)
    # Save the search to the database
    db.save_search(user_text, reply)
    return jsonify({"response": reply})

if __name__ == "__main__":
    # Run Flask in debug mode for development
    app.run(debug=True)

  if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
