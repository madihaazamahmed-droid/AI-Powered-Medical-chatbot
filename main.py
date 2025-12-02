
import os
import io
import base64
import logging
from flask import Flask, request, jsonify, render_template                                       # type: ignore
from PIL import Image                                                                            # type: ignore
import requests                                                                                  # type: ignore
from dotenv import load_dotenv                                                                   # type: ignore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

if not GROQ_API_KEY:
    raise ValueError("Missing GROQ API key. Please add GROQ_API_KEY to your .env file.")

app = Flask(__name__)

def _format_as_bullets(text: str) -> str:
    try:
        lines = [ln.strip() for ln in (text or "").split("\n")]
        bullet_lines = []
        for ln in lines:
            if not ln:
                continue
            clean = ln.lstrip("*-• ")
            if clean:
                bullet_lines.append(f"- {clean}")
        return "\n".join(bullet_lines) if bullet_lines else (text or "")
    except Exception:
        return text

def process_image(image_content, query):
    try:
        encoded_image = base64.b64encode(image_content).decode("utf-8")

        try:
            img = Image.open(io.BytesIO(image_content))
            img.verify()
        except Exception as e:
            return {"error": "We couldn't read that image. Please upload a valid JPG or PNG."}

        messages = [
            {
                "role": "system",
                "content": [{"type": "text", "text": "You are a helpful medical assistant. Respond ONLY in concise bullet points. Each point should be a short, clear sentence."}]
            },
            {
            "role": "user", 
            "content": [{
                "type": "text", 
                "text": f"Please answer in concise bullet points.\n\n{query}"
            }, {
                "type": "image_url", 
                "image_url": {
                    "url": f"data:image/jpeg;base64,{encoded_image}"
                }
            }]
        }]

        def make_api_request(model):
            try:
                response = requests.post(
                    GROQ_API_URL,
                    json={
                        "model": model,
                        "messages": messages,
                        "max_tokens": 1000
                    },
                    headers={
                        "Authorization": f"Bearer {GROQ_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    return response.json()["choices"][0]["message"]["content"]
                else:
                    return f"The AI service returned an error (HTTP {response.status_code}). Please try again."
                    
            except requests.exceptions.Timeout:
                return "Request timed out. Please try again."
            except requests.exceptions.RequestException as e:
                return "We couldn't reach the AI service. Please check your connection and try again."

        scout = make_api_request("meta-llama/llama-4-scout-17b-16e-instruct")
        maverick = make_api_request("meta-llama/llama-4-maverick-17b-128e-instruct")

        combined_text = "\n".join([str(scout or ""), str(maverick or "")])
        formatted = _format_as_bullets(combined_text)
        return {"response": formatted}
        
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        return {"error": "Something went wrong while processing the image. Please try again."}

def process_text(query):
    try:
        messages = [
            {
                "role": "system",
                "content": [{"type": "text", "text": "You are a helpful medical assistant. Respond ONLY in concise bullet points. Each point should be a short, clear sentence."}]
            },
            {
                "role": "user",
                "content": [{"type": "text", "text": f"Please answer in concise bullet points.\n\n{query}"}]
            }
        ]

        response = requests.post(
            GROQ_API_URL,
            json={
                "model": "meta-llama/llama-4-scout-17b-16e-instruct",
                "messages": messages,
                "max_tokens": 1000
            },
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            timeout=30
        )

        if response.status_code == 200:
            raw = response.json()["choices"][0]["message"]["content"]
            return {"response": _format_as_bullets(raw)}
        return {"error": f"The AI service returned an error (HTTP {response.status_code}). Please try again."}

    except requests.exceptions.Timeout:
        return {"error": "Request timed out. Please try again."}
    except requests.exceptions.RequestException:
        return {"error": "We couldn't reach the AI service. Please check your connection and try again."}
    except Exception as e:
        logger.error(f"Error processing text: {str(e)}")
        return {"error": "Something went wrong while processing your request. Please try again."}

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        if "image" not in request.files:
            return jsonify({"error": "Please attach an image to analyze."}), 400
        
        image_file = request.files["image"]

        if image_file.filename == '':
            return jsonify({"error": "Please choose an image file to upload."}), 400

        query = request.form.get("query", "Please analyze this medical image and explain your findings.")

        image_content = image_file.read()

        if len(image_content) > 10 * 1024 * 1024:
            return jsonify({"error": "The image is too large (max 10MB). Please upload a smaller file."}), 400

        result = process_image(image_content, query)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in analyze endpoint: {str(e)}")
        return jsonify({"error": "Something went wrong on our side. Please try again."}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Sorry, we couldn't find that page."}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Something went wrong on our side. Please try again."}), 500

@app.route("/chat", methods=["POST"])
def chat():
    try:
        if request.is_json:
            data = request.get_json(silent=True) or {}
            text = data.get("text", "").strip()
            image_data_url = data.get("image_data_url")
        else:
            text = request.form.get("text", "").strip()
            image_data_url = request.form.get("image_data_url")

        if not text and not image_data_url:
            return jsonify({"error": "Please provide a message or an image to analyze."}), 400

        if image_data_url:
            try:
                header, b64data = image_data_url.split(",", 1)
                image_bytes = base64.b64decode(b64data)
            except Exception:
                return jsonify({"error": "Invalid image data. Please re-upload the image."}), 400
            result = process_image(image_bytes, text or "Please analyze this medical image and explain your findings.")
            return jsonify(result)

        result = process_text(text)
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({"error": "Something went wrong on our side. Please try again."}), 500

if __name__ == "__main__":
    ssl_context = 'adhoc' if os.getenv("USE_HTTPS") == "1" else None
    app.run(host="0.0.0.0", port=5000, debug=True, ssl_context=ssl_context)