import json
import os
import re

from google import genai


PROMPT_BASE = """Eres un asistente especializado en análisis de documentos escolares para la plataforma ComuCole.
A continuación recibirás el texto crudo extraído de un documento .docx de planificación docente.

Tu tarea es extraer ESTRICTAMENTE los siguientes bloques y devolver SOLO un JSON válido (sin markdown, sin ```json, sin texto adicional):

1. "resumen_sesion": Un resumen amigable y ejecutivo (máximo 2 párrafos) basado en el cuadro extenso de "Desarrollo de la Actividad".

2. "tarea": La instrucción exacta para la casa. Está camuflada dentro del sub-apartado "- Cierre" ubicado al final del cuadro de desarrollo. Extrae SOLO la instrucción de la tarea.

3. "materiales": Lista de útiles o recursos si el docente los solicita explícitamente en el texto para algún día en particular. Si no hay materiales, devuelve una lista vacía [].

4. "semaforo": Clasificación del tiempo de entrega en UNO de estos 3 strings exactos:
   - "rojo" -> Es para ya / mucha carga
   - "amarillo" -> Tienes tiempo / plazo moderado
   - "verde" -> Vas bien de tiempo / plazo amplio

5. "categoria": Clasificación del tipo de trabajo en UNO de estos 3 strings exactos:
   - "cognitivo" -> Estudio, lectura, matemática
   - "manual" -> Maquetas, arte, materiales
   - "psicomotriz" -> Educación física o actividades motrices

REGLAS ESTRICTAS:
- Devuelve SOLO el JSON. No expliques tu razonamiento.
- No inventes información. Si un campo no está presente, usa valores por defecto (lista vacía para materiales).
- El JSON debe ser parseable directamente con json.loads().
- Usa exactamente las claves: resumen_sesion, tarea, materiales, semaforo, categoria.

TEXTO DEL DOCUMENTO:
"""


def _limpiar_json_respuesta(texto: str) -> str:
    texto = texto.strip()
    if texto.startswith("```"):
        texto = re.sub(r"^```(?:json)?\s*", "", texto)
        texto = re.sub(r"\s*```$", "", texto)
    return texto.strip()


def procesar_documento_con_gemini(texto_crudo: str) -> dict:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY no está definida en las variables de entorno.")

    cliente = genai.Client(api_key=api_key)

    prompt = PROMPT_BASE + texto_crudo
    respuesta = cliente.models.generate_content(model="gemini-1.5-flash", contents=prompt)
    texto_respuesta = respuesta.text

    json_limpio = _limpiar_json_respuesta(texto_respuesta)
    datos = json.loads(json_limpio)

    return {
        "resumen_sesion": datos.get("resumen_sesion", ""),
        "tarea": datos.get("tarea", ""),
        "materiales": datos.get("materiales", []),
        "semaforo": datos.get("semaforo", "amarillo"),
        "categoria": datos.get("categoria", "cognitivo"),
    }
