// Greeting (loads the welcome message from Flask)
async function loadGreeting() {
  try {
    let response = await fetch("http://127.0.0.1:5000/");
    let data = await response.json();
    addMessage("🌍 Gemini Travel Assistant: " + data.message, "bot");
  } catch (err) {
    addMessage("⚠️ Could not load greeting.", "bot");
  }
}

// Sending a chat message to the backend
async function sendMessage() {
  let input = document.getElementById("userInput");
  let userText = input.value.trim();

  if (!userText) return;

  // Show user message
  addMessage(userText, "user");
  
  // Show thinking message (with an ID to remove later)
  let thinkingMsg = addMessage("⏳ Gemini is thinking...", "bot", true);
  
  try {
    let response = await fetch("http://127.0.0.1:5000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: userText })
    });

    let data = await response.json();

    // Remove thinking message
    thinkingMsg.remove();
    
    // Show Gemini response
    addMessage("🤖 Gemini: " + data.response, "bot");
  } catch (err) {
    // Remove thinking message in case of error
    thinkingMsg.remove();
    addMessage("⚠️ Error: Could not reach Gemini server.", "bot");
  }

  // Clear the input field
  input.value = "";
}

// Helper to add messages to chat
function addMessage(text, sender, isThinking = false) {
  let chatbox = document.getElementById("messages");
  let msg = document.createElement("div");
  msg.className = "message " + sender;
  msg.innerText = text;
  
  // Add an ID to the thinking message so we can remove it later
  if (isThinking) {
    msg.id = "thinking-msg";
  }

  chatbox.appendChild(msg);
  chatbox.scrollTop = chatbox.scrollHeight;

  return msg; // Return the message element to control removal later
}


// Load greeting on page start
window.onload = loadGreeting;
