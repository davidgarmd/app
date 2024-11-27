import os
from flask import Flask, request, jsonify
import openai
import json
from dotenv import load_dotenv
from flask_cors import CORS

# Cargar variables de entorno desde el archivo .env
load_dotenv()

app = Flask(__name__)
CORS(app)  # Habilita CORS para el frontend

# Cargar la clave de OpenAI desde las variables de entorno
openai.api_key = os.getenv("OPENAI_API_KEY")

# Verificar si la clave se cargó correctamente
if not openai.api_key:
    raise ValueError("No se encontró la clave de OpenAI en el archivo .env")

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

@app.route("/chat", methods=["POST"])
def chat():
    # Capturar la entrada del usuario
    user_input = request.json.get("message", "").strip()

    # Buscar en la base de conocimiento
    answer_data = find_answer(user_input)

    # Si se encuentra una respuesta, devolver la información
    if answer_data:
        return jsonify({
            "response": answer_data["answer"],
            "metadata": {
                "category": answer_data["category"],
                "subcategory": answer_data["subcategory"],
                "tags": answer_data["tags"]
            }
        })

    # Si no se encuentra respuesta, usar GPT-4 para generar una respuesta
    try:
        # Nueva forma de usar la API
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un asistente médico experto en cirugía vascular."},
                {"role": "user", "content": user_input},
            ],
            temperature=0.7,  # Controla la creatividad
        )
        gpt_response = response.choices[0].message.content
    except Exception as e:
        gpt_response = "Lo siento, hubo un problema al procesar tu solicitud. Por favor, intenta nuevamente."
        print(f"Error con OpenAI API: {e}")

    return jsonify({"response": gpt_response})

if __name__ == "__main__":
    app.run(debug=True)

    # Solo ejecutar si el archivo se ejecuta directamente
if __name__ == "__main__":
    # Configuración para desarrollo local o despliegue
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))