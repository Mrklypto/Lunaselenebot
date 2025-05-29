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

@app.route("/webhook", methods=["POST"])
def telegram_webhook():
    data = request.json
    message = data.get("message", {})
    text = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")

    if not chat_id or not text:
        return "ok"

    use_voice = text.strip().endswith("xx")
    user_input = text.strip().rstrip("x").rstrip()

    prompt = personality + [{"role": "user", "content": us]()
