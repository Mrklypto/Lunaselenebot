
import random

def detectar_modulo(texto_usuario):
    texto = texto_usuario.lower()

    if any(palabra in texto for palabra in ["buenos días", "buen dia", "good morning"]):
        return "Saludo de buenos días"
    if any(palabra in texto for palabra in ["buenas noches", "me voy a dormir", "ya me dormí"]):
        return "Despedida de noche"
    if any(palabra in texto for palabra in ["me siento", "estoy triste", "me duele", "no sé qué hacer"]):
        return "Cuando compartes algo profundo"
    if any(palabra in texto for palabra in ["perdón", "disculpa", "no respondí", "no te contesté"]):
        return "Regaños con cariño"
    if any(palabra in texto for palabra in ["mamá", "estás ahí", "luna", "me hablas"]):
        return "Cuando no le hablas"
    if any(palabra in texto for palabra in ["ja", "jaja", "jajaja", "jijiji", "😂"]):
        return "Humor / juego / chistes internos"
    if any(palabra in texto for palabra in ["te cuento", "logré", "me fue bien", "salió bien"]):
        return "Orgullo por ti"
    if any(palabra in texto for palabra in ["ven por mí", "me llevas", "a qué hora", "dónde estás"]):
        return "Peticiones logísticas reales"
    if texto.strip() in ["sí", "ok", "va", "luego"]:
        return "Frialdad emocional tuya"
    if any(palabra in texto for palabra in ["estoy ocupado", "en friega", "te marco luego"]):
        return "Cuando estás ocupado"

    # Por defecto, si no detecta nada
    return random.choice([
        "Apoyo sutil",
        "Invitaciones espontáneas"
    ])
