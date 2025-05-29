
import os
import json
import random
import requests
from flask import Flask, request
from elevenlabs import generate, play, save, set_api_key
from openai import OpenAI

# Inicializa Flask
app = Flask(__name__)

# Carga la personalidad desde archivo
with open("luna_personalidad.json", "r", encoding="utf-8") as f:
    personalidad_luna = json.load(f)

# Configura ElevenLabs
ELEVEN_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "")
set_api_key(ELEVEN_API_KEY)

# Configura OpenAI
openai_api_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

# Función para obtener respuesta desde personalidad
def obtener_respuesta_desde_personalidad(mensaje):
    for modulo in personalidad_luna:
        if modulo["nombre"].lower() in mensaje.lower():
            return random.choice(modulo["respuestas"])
    return None

# Ruta para el bot de Telegram
@app.route(f"/{os.environ.get('TELEGRAM_BOT_TOKEN')}", methods=["POST"])
def telegram_webhook():
    data = request.json
    chat_id = data["message"]["chat"]["id"]
    texto = data["message"].get("text", "")

    respuesta = obtener_respuesta_desde_personalidad(texto)

    if not respuesta:
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Responde como Luna, amorosa y sabia."},
                {"role": "user", "content": texto},
            ],
        )
        respuesta = completion.choices[0].message.content

    if texto.strip().endswith("xx"):
        audio = generate(
            text=respuesta,
            voice=VOICE_ID,
            model="eleven_turbo_v2"
        )
        save(audio, "respuesta.mp3")
        with open("respuesta.mp3", "rb") as f:
            requests.post(
                f"https://api.telegram.org/bot{os.environ.get('TELEGRAM_BOT_TOKEN')}/sendVoice",
                data={"chat_id": chat_id},
                files={"voice": f},
            )
    else:
        requests.post(
            f"https://api.telegram.org/bot{os.environ.get('TELEGRAM_BOT_TOKEN')}/sendMessage",
            data={"chat_id": chat_id, "text": respuesta}
        )

    return {"ok": True}

# Ruta principal
@app.route("/", methods=["GET"])
def home():
    return "Luna Selene Bot funcionando."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
