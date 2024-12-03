import os
from flask import Flask, request, jsonify
import openai
import json
from dotenv import load_dotenv
from flask_cors import CORS
import requests  # Para realizar solicitudes HTTP

# Cargar variables de entorno desde el archivo .env
load_dotenv()

app = Flask(__name__)
CORS(app)  # Habilita CORS para el frontend

# Cargar la clave de OpenAI desde las variables de entorno
openai.api_key = os.getenv("OPENAI_API_KEY")

# Cargar las claves de la API de WhatsApp
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")

# Verificar si las claves se cargaron correctamente
if not openai.api_key:
    raise ValueError("No se encontró la clave de OpenAI en el archivo .env")
if not WHATSAPP_ACCESS_TOKEN or not PHONE_NUMBER_ID or not VERIFY_TOKEN:
    raise ValueError("No se encontraron todas las claves necesarias en el archivo .env")

# Cargar la base de conocimiento desde el archivo JSON
with open("knowledge_base.json", encoding="utf-8") as f:
    knowledge_base = json.load(f)

# Función para buscar respuestas en la base de conocimiento
def find_answer(user_question):
    for entry in knowledge_base:
        if entry["question"].lower() in user_question.lower():
            return {
                "answer": entry["answer"],
                "category": entry["category"],
                "subcategory": entry["subcategory"],
                "tags": entry["tags"]
            }
    return None

# Función para enviar mensajes a través de WhatsApp API
def send_whatsapp_message(recipient_id, message):
    url = f"https://graph.facebook.com/v16.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": recipient_id,
        "type": "text",
        "text": {"body": message},
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()

# Endpoint para recibir mensajes de WhatsApp (webhook)
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    try:
        # Verificar si el mensaje es válido
        if "messages" in data["entry"][0]["changes"][0]["value"]:
            message = data["entry"][0]["changes"][0]["value"]["messages"][0]
            sender_id = message["from"]  # Número del usuario que envió el mensaje
            user_message = message["text"]["body"]  # Texto enviado por el usuario

            # Buscar respuesta en la base de conocimiento
            answer_data = find_answer(user_message)

            if answer_data:
                reply = answer_data["answer"]
            else:
                # Usar GPT-4 si no hay respuesta en la base de conocimiento
                try:
                    response = openai.ChatCompletion.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": "Eres un asistente médico experto en cirugía vascular."},
                            {"role": "user", "content": user_message},
                        ],
                        temperature=0.7,
                    )
                    reply = response.choices[0].message["content"]
                except Exception as e:
                    reply = "Lo siento, hubo un problema al procesar tu solicitud. Por favor, intenta nuevamente."
                    print(f"Error con OpenAI API: {e}")

            # Enviar respuesta al usuario a través de WhatsApp
            send_whatsapp_message(sender_id, reply)
    except Exception as e:
        print(f"Error procesando el webhook: {e}")
    return "EVENT_RECEIVED", 200

# Endpoint para la verificación del webhook de WhatsApp
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("Webhook verificado.")
            return challenge, 200
        else:
            return "Error de verificación", 403
    return "Nada que procesar", 404

# Solo ejecutar si el archivo se ejecuta directamente
if __name__ == "__main__":
    # Configuración para desarrollo local o despliegue
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))