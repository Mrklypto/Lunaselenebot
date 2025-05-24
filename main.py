
import os
import json
import logging
from flask import Flask, request
import requests
from openai import OpenAI
from elevenlabs import generate, play, save
from elevenlabs.client import ElevenLabs

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")
ELEVEN_KEY = os.getenv("ELEVENLABS_API_KEY")

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Cargar dataset local
with open("luna_personality_dataset.json", "r", encoding="utf-8") as f:
    personality = json.load(f)

# Ruta para webhook de Telegram
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def telegram_webhook():
    data = request.json
    message = data.get("message", {})
    text = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")

    if not chat_id or not text:
        return "ok"

    # Determinar si debe responder con voz
    use_voice = text.strip().endswith("xx")
    user_input = text.strip().rstrip("x").rstrip()

    # Crear prompt con personalidad
    prompt = personality + [{"role": "user", "content": user_input}]

    # Llamar a OpenAI para generar respuesta
    openai = OpenAI()
    completion = openai.chat.completions.create(
        model="gpt-4",
        messages=prompt,
        temperature=0.8,
    )
    reply = completion.choices[0].message.content

    if use_voice:
        # Generar voz con ElevenLabs
        client = ElevenLabs(api_key=ELEVEN_KEY)
        audio = client.generate(text=reply, voice=VOICE_ID, model="eleven_monolingual_v1")
        path = "output.mp3"
        save(audio, path)
        send_voice(chat_id, path)
    else:
        send_message(chat_id, reply)

    return "ok"

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
    app.run(host="0.0.0.0", port=10000)
