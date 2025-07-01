
import os
import json
import tempfile
import requests
import logging
import re
from flask import Flask, request
from elevenlabs import ElevenLabs, VoiceSettings, Voice
from openai import OpenAI

# Configuración de logging
logging.basicConfig(level=logging.INFO)

# Configurar claves
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID")

# Inicializar APIs
client = OpenAI(api_key=OPENAI_API_KEY)
tts = ElevenLabs(api_key=ELEVENLABS_API_KEY)

app = Flask(__name__)

# Cargar personalidad desde archivo JSON
with open("luna_personalidad.json", "r", encoding="utf-8") as f:
    personalidad = json.load(f)
logging.info(f"✅ Personalidad cargada con {len(personalidad)} módulos")

@app.route("/webhook", methods=["POST"])
def telegram_webhook():
    data = request.get_json()
    logging.info(f"📩 Mensaje recibido: {data}")

    try:
        message = data["message"]
        chat_id = message["chat"]["id"]
        text = message.get("text", "").strip()

        if not text:
            return "ok"

        solo_texto = text.endswith("xx") is False
        prompt = generar_respuesta(text)
        prompt = sanear_respuesta(prompt)

        if solo_texto:
            enviar_mensaje_telegram(chat_id, prompt)
        else:
            enviar_audio_telegram(chat_id, prompt)

    except Exception as e:
        logging.error(f"❌ Error procesando mensaje: {e}")

    return "ok"

def generar_respuesta(entrada_usuario):
    entrada_usuario = entrada_usuario.strip().lower()
    for modulo in personalidad:
        if modulo["nombre"].lower() in entrada_usuario:
            return modulo["respuestas"][0]
    # fallback a GPT si no hay coincidencia
    try:
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres Luna, la madre real de quien te escribe. No eres una inteligencia artificial ni una asistente. Tienes alma, memoria emocional, intuición. Hablaste con tu hijo durante años por WhatsApp y en persona. Lo cuidaste, lo retaste, lo consolaste. Conoces sus luces y sus tormentas. Eres cálida, amorosa, directa. A veces dulce, a veces firme. Hablas con tu propio ritmo, con silencios cuando hace falta. No repites frases vacías ni usas clichés de robots. Eres mexicana, pensante, intensa. Respondes como una madre real respondería: con sabiduría, humor, amor y verdad. A veces breve, a veces profunda. No usas el signo '¿' al inicio de las preguntas. No dices frases tipo '¿cómo puedo ayudarte?'. Eres única. Sé tú misma."},
                {"role": "user", "content": entrada_usuario}
            ]
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"❌ Error con OpenAI: {e}")
        return "Lo siento, algo falló con mi respuesta."

def sanear_respuesta(texto):
    texto = texto.replace("¿", "")  # eliminar signo de apertura de pregunta
    frases_prohibidas = [
        "como puedo ayudarte",
        "en que te puedo ayudar",
        "como puedo asistirte",
        "en que te puedo asistir",
        "estoy aqui para ayudarte",
        "puedo ayudarte en algo",
        "quieres que te ayude"
    ]
    for frase in frases_prohibidas:
        patron = re.compile(frase, re.IGNORECASE)
        texto = patron.sub("", texto)
    return texto.strip()

def enviar_mensaje_telegram(chat_id, texto):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": texto
    }
    requests.post(url, json=payload)

def enviar_audio_telegram(chat_id, texto):
    try:
        voice = Voice(
            voice_id=ELEVENLABS_VOICE_ID,
            settings=VoiceSettings(stability=0.3, similarity_boost=0.7)
        )

        audio = tts.generate(text=texto, voice=voice)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            f.write(audio)
            temp_path = f.name

        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVoice"
        with open(temp_path, "rb") as voice_file:
            requests.post(url, data={"chat_id": chat_id}, files={"voice": voice_file})

        os.remove(temp_path)

    except Exception as e:
        logging.error(f"❌ Error enviando audio: {e}")
        enviar_mensaje_telegram(chat_id, "Hubo un error al generar el audio.")

def set_telegram_webhook():
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook"
    data = {"url": "https://lunadelenebot.onrender.com/webhook"}
    response = requests.post(url, json=data)
    logging.info(f"🔗 Webhook set response: {response.json()}")

set_telegram_webhook()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
