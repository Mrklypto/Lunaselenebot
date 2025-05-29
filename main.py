import os
import json
import logging
import random
import requests
from flask import Flask, request
from openai import OpenAI
from decision_map import detectar_modulo

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "xyngy2IvgfMUGnF0n5Ew")
ELEVEN_KEY = os.getenv("ELEVENLABS_API_KEY")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

openai = OpenAI(api_key=OPENAI_KEY)

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Cargar personalidad
try:
    with open("luna_personalidad.json", "r", encoding="utf-8") as f:
        personalidad = json.load(f)
    print(f"✅ Personalidad cargada con {len(personalidad)} módulos")
except Exception as e:
    print("❌ Error cargando personalidad:", str(e))
    personalidad = []

@app.before_first_request
def mostrar_saldos():
    try:
        # OPENAI balance
        openai_balance = requests.get(
            "https://api.openai.com/dashboard/billing/credit_grants",
            headers={"Authorization": f"Bearer {OPENAI_KEY}"}
        ).json().get("total_available", "¿?")
        print(f"💰 OpenAI balance: ${openai_balance}")

        # ELEVEN balance
        eleven_balance = requests.get(
            "https://api.elevenlabs.io/v1/user/subscription",
            headers={"xi-api-key": ELEVEN_KEY}
        ).json().get("available_character_count", "¿?")
        print(f"🗣️ ElevenLabs tokens disponibles: {eleven_balance}")
    except Exception as e:
        print("⚠️ Error al consultar saldos:", str(e))

@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def telegram_webhook():
    data = request.json
    message = data.get("message", {})
    text = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")

    if not chat_id or not text:
        return "ok"

    use_voice = text.strip().endswith("xx")
    cleaned_text = text.strip().rstrip("x").rstrip()

    respuesta = obtener_respuesta(cleaned_text)

    try:
        if use_voice:
            voice_path = generar_audio(respuesta)
            enviar_audio(chat_id, voice_path)
        else:
            enviar_texto(chat_id, respuesta)
    except Exception as e:
        logging.exception("❌ Error enviando respuesta")
        enviar_texto(chat_id, "Lo siento, hubo un error generando la respuesta.")

    return "ok"

def obtener_respuesta(texto_usuario):
    modulo = detectar_modulo(texto_usuario)
    if not modulo:
        return "Cuéntame más, mi amor..."

    opciones = next((x["respuestas"] for x in personalidad if x["nombre"] == modulo), [])
    if not opciones:
        return "Estoy aquí, mi vida. Te escucho."

    return random.choice(opciones)["texto"]

def generar_audio(texto):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {
        "xi-api-key": ELEVEN_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": texto,
        "model_id": "eleven_turbo_v2",
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

def enviar_texto(chat_id, texto):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": texto})

def enviar_audio(chat_id, path):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVoice"
    with open(path, "rb") as f:
        requests.post(url, files={"voice": f}, data={"chat_id": chat_id})

@app.route("/", methods=["GET"])
def home():
    return "LunaBot corriendo 💙"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
