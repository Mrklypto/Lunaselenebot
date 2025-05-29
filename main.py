
import os
import json
import random
import logging
from flask import Flask, request
from elevenlabs import generate, save, Voice, VoiceSettings, play_audio, set_api_key
from openai import OpenAI
import requests

# Configuración básica
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# API Keys
openai.api_key = os.getenv("OPENAI_API_KEY")
set_api_key(os.getenv("ELEVENLABS_API_KEY"))

# Cargar personalidad
with open("luna_personalidad.json", "r", encoding="utf-8") as f:
    personalidad_luna = json.load(f)
    logging.info(f"✅ Personalidad cargada con {len(personalidad_luna)} módulos")

def elegir_respuesta(modulo):
    for item in personalidad_luna:
        if item["nombre"] == modulo:
            return random.choice(item["respuestas"])
    return "No entendí eso."

@app.route("/", methods=["GET"])
def home():
    return "LunaSeleneBot funcionando."

@app.route(f"/{os.getenv('TELEGRAM_BOT_TOKEN')}", methods=["POST"])
def webhook():
    data = request.json

    if "message" not in data:
        return {"ok": True}

    message = data["message"]
    chat_id = message["chat"]["id"]

    # Mensaje de texto
    if "text" in message:
        user_input = message["text"]
        logging.info(f"📩 Mensaje recibido: {user_input}")

        if user_input.lower().endswith("xx"):
            prompt = user_input[:-2].strip()
            response_text = elegir_respuesta("Saludo de buenos días")  # ejemplo fijo
            audio = generate(
                text=response_text,
                voice=Voice(
                    voice_id=os.getenv("ELEVENLABS_VOICE_ID"),
                    settings=VoiceSettings(stability=0.3, similarity_boost=0.75)
                ),
                model="eleven_turbo_v2"
            )
            save(audio, "voz.mp3")
            send_audio(chat_id, "voz.mp3")
        else:
            response_text = elegir_respuesta("Saludo de buenos días")  # ejemplo fijo
            send_message(chat_id, response_text)

    return {"ok": True}

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

def send_audio(chat_id, audio_path):
    url = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/sendAudio"
    with open(audio_path, "rb") as f:
        requests.post(url, files={"audio": f}, data={"chat_id": chat_id})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
