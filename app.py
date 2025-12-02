from flask import Flask, request, jsonify, render_template_string                                # type: ignore
import base64
import requests                                                                                 # type: ignore
import io
from PIL import Image                                                                           # type: ignore
from dotenv import load_dotenv                                                                     # type: ignore
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is not set in the .env file")

def process_image(image_data, query):
    try:
        image_content = base64.b64decode(image_data.split(',')[1])
        encoded_image = base64.b64encode(image_content).decode("utf-8")
        
        try:
            Image.open(io.BytesIO(image_content)).verify()
        except Exception:
            return {"error": "We couldn't read that image. Please upload a valid JPG or PNG."}

        prompt = f"Analyze this medical image and answer: {query}"

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}}
                ]
            }
        ]

        response = requests.post(
            GROQ_API_URL,
            json={
                "model": "meta-llama/llama-4-scout-17b-16e-instruct",
                "messages": messages,
                "max_tokens": 1000,
                "temperature": 0.2
            },
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            timeout=30
        )

        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"]
            return {"response": content}
        else:
            return {"error": f"API error: {response.status_code}"}

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {"error": "Something went wrong. Please try again."}

def process_text(query):
    try:
        messages = [
            {
                "role": "user",
                "content": [{"type": "text", "text": query}]
            }
        ]

        response = requests.post(
            GROQ_API_URL,
            json={
                "model": "meta-llama/llama-4-scout-17b-16e-instruct",
                "messages": messages,
                "max_tokens": 1000,
                "temperature": 0.2
            },
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            timeout=30
        )

        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"]
            return {"response": content}
        else:
            return {"error": f"API error: {response.status_code}"}

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {"error": "Something went wrong. Please try again."}

@app.route("/", methods=["GET"])
def home():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>Medical Chatbot</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 800px; margin: 0 auto; }
        .message { margin: 10px 0; padding: 10px; border-radius: 5px; }
        .user { background: #e3f2fd; }
        .bot { background: #f5f5f5; }
        input, textarea { width: 100%; padding: 10px; margin: 5px 0; }
        button { padding: 10px 20px; background: #2196f3; color: white; border: none; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Medical Chatbot</h1>
        <div id="messages"></div>
        <input type="file" id="imageInput" accept="image/*">
        <textarea id="messageInput" placeholder="Ask a medical question..."></textarea>
        <button onclick="sendMessage()">Send</button>
    </div>
    <script>
        function sendMessage() {
            const text = document.getElementById('messageInput').value;
            const imageInput = document.getElementById('imageInput');
            
            if (!text && !imageInput.files[0]) return;
            
            addMessage('user', text);
            
            const formData = new FormData();
            if (imageInput.files[0]) {
                formData.append('image', imageInput.files[0]);
            }
            if (text) {
                formData.append('text', text);
            }
            
            fetch('/chat', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    addMessage('bot', 'Error: ' + data.error);
                } else {
                    addMessage('bot', data.response);
                }
            });
            
            document.getElementById('messageInput').value = '';
            imageInput.value = '';
        }
        
        function addMessage(sender, text) {
            const div = document.createElement('div');
            div.className = 'message ' + sender;
            div.textContent = text;
            document.getElementById('messages').appendChild(div);
        }
    </script>
</body>
</html>
    """)

@app.route("/chat", methods=["POST"])
def chat():
    try:
        text = request.form.get("text", "").strip()
        image_file = request.files.get("image")
        
        if not text and not image_file:
            return jsonify({"error": "Please provide a message or image"})
        
        if image_file:
            image_content = image_file.read()
            image_data = "data:image/jpeg;base64," + base64.b64encode(image_content).decode("utf-8")
            result = process_image(image_data, text or "What do you see in this image?")
        else:
            result = process_text(text)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return jsonify({"error": "Something went wrong"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)