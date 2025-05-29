import os
import json
import logging
from flask import Flask, request
import requests
import openai

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")
ELEVEN_KEY = os.getenv("ELEVENLABS_API_KEY")
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

try:
    with open("luna_personality_dataset.json", "r", encoding="utf-8") as f:
        personality = json.load(f)
        print(f"✅ Personalidad cargada con {len(personality)} mensajes")
except Exception as e:
    print("❌ Error cargando personalidad:", str(e))
    personality = []

@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def telegram_webhook():
    data = request.json
    message = data.get("message", {})
    text = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")

    if not chat_id or not text:
        return "ok"

    use_voice = text.strip().endswith("xx")
    user_input = text.strip().rstrip("x").rstrip()

    prompt = personality + [{"role": "user", "content": user_input}]
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4",
            messages=prompt,
            temperature=0.8
        )
        reply = completion.choices[0].message.content

        if use_voice:
            voice_path = generate_audio(reply)
            send_voice(chat_id, voice_path)
        else:
            send_message(chat_id, reply)

    except Exception as e:
        logging.exception("❌ Error al generar respuesta:")
        send_message(chat_id, "Lo siento, hubo un error generando la respuesta.")

    return "ok"

def generate_audio(text):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {
        "xi-api-key": ELEVEN_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    path = "output.mp3"
    with open(path, "wb") as f:
        f.write(response.content)
    return path

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)

def send_voice(chat_id, path):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVoice"
    with open(path, "rb") as audio_file:
        files = {"voice": audio_file}
        data = {"chat_id": chat_id}
        requests.post(url, files=files, data=data)

@app.route("/", methods=["GET"])
def home():
    return "LunaBot Running"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
