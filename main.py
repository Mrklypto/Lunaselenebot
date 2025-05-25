import os
import json
import logging
from flask import Flask, request
import requests
from openai import OpenAI

# 🔥 Eliminar proxies que rompen OpenAI en algunas instalaciones
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)

# Variables de entorno
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")
ELEVEN_KEY = os.getenv("ELEVENLABS_API_KEY")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

print("✅ TELEGRAM_TOKEN:", TELEGRAM_TOKEN[:10] if TELEGRAM_TOKEN else "❌ VACÍO")
print("✅ OPENAI_KEY:", OPENAI_KEY[:10] if OPENAI_KEY else "❌ VACÍO")
print("✅ ELEVEN_KEY:", ELEVEN_KEY[:10] if ELEVEN_KEY else "❌ VACÍO")
print("✅ VOICE_ID:", VOICE_ID if VOICE_ID else "❌ VACÍO")

# Cliente de OpenAI
client = OpenAI(api_key=OPENAI_KEY)

# Flask setup
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Cargar personalidad
try:
    with open("luna_personality_dataset.json", "r", encoding="utf-8") as f:
        personality = json.load(f)
        print(f"✅ Personalidad cargada con {len(personality)} mensajes")
except Exception as e:
    print("❌ Error cargando personalidad:", str(e))
    personality = []

@app.route("/webhook", methods=["GET", "POST"])
def telegram_webhook():
    logging.info(f"✅ Webhook recibido: {request.method}")

    if request.method == "GET":
        return "Webhook activo"

    data = request.json
    message = data.get("message", {})
    text = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")

    if not chat_id or not text:
        print("⚠️ No se encontró chat_id o texto.")
        return "ok"

    use_voice = text.strip().endswith("xx")
    user_input = text.strip().rstrip("x").rstrip()

    prompt = personality + [{"role": "user", "content": user_input}]
    print("🧠 Prompt enviado:")
    for m in prompt:
        print(f"{m['role']}: {m['content'][:80]}...")

    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
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
    app.run(host="0.0.0.0", port=10000)
