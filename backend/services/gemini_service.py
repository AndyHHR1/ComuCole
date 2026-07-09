import json
import logging
import os
import re

from google import genai
from google.genai import errors as genai_errors

logger = logging.getLogger(__name__)

PROMPT_BASE = """Eres un asistente especializado en análisis de documentos escolares para la plataforma ComuCole.
A continuación recibirás el texto crudo extraído de un documento .docx de planificación docente.

Tu tarea es extraer ESTRICTAMENTE los siguientes bloques y devolver SOLO un JSON válido (sin markdown, sin ```json, sin texto adicional):

1. "resumen_sesion": Un resumen amigable y ejecutivo (máximo 2 párrafos) basado en el cuadro extenso de "Desarrollo de la Actividad". Resume lo que los niños hicieron en la sesión, qué aprendieron y cómo trabajaron.

2. "tarea": La instrucción exacta para la casa. Busca en el apartado "CIERRE" ubicado al final del documento. REGLAS DE ORO PARA EXTRAER LA TAREA:
   - En el CIERRE casi siempre aparecen PRIMERO las preguntas de reflexión oral para los niños (ejemplo: "¿Qué aprendimos hoy?", "¿Cómo descubrimos las semejanzas?", etc.). Esas preguntas NO son la tarea.
   - Después de las preguntas de reflexión, el docente suele escribir frases como "Escucho sus respuestas y retroalimento..." o "Reforzamos las ideas principales...". Tampoco son la tarea.
   - La tarea real suele venir DESPUÉS de eso, frecuentemente introducida con frases como:
     * "Finalmente, entrego una hoja gráfica..."
     * "Como actividad final, ..."
     * "Para la casa: ..."
     * "Tarea: ..."
     * "Actividad para casa: ..."
     * "Realizar en casa: ..."
     * "Como tarea, ..."
     * "Se entrega una ficha/hoja gráfica..."
   - Extrae SOLO la instrucción/actividad concreta para la casa, NO las preguntas de reflexión.
   - Si no encuentras ninguna actividad concreta para la casa, devuelve un string vacío "".

3. "materiales": Lista de útiles o recursos si el docente los solicita explícitamente en el texto. Busca en secciones como "RECURSOS Y MATERIALES SUGERIDOS" o frases como "materiales", "útiles", "necesitan", "llevar", "recursos", "hoja gráfica", "ficha", "tarjetas", "imágenes". Si no hay materiales, devuelve una lista vacía [].

4. "semaforo": Clasificación del tiempo de entrega en UNO de estos 3 strings exactos:
   - "rojo" -> Es para ya / mucha carga
   - "amarillo" -> Tienes tiempo / plazo moderado
   - "verde" -> Vas bien de tiempo / plazo amplio

5. "categoria": Clasificación del tipo de trabajo en UNO de estos 3 strings exactos:
   - "cognitivo" -> Estudio, lectura, matemática, reconocer semejanzas y diferencias,observar imágenes
   - "manual" -> Maquetas, arte, materiales, recortar, pegar, armar
   - "psicomotriz" -> Educación física o actividades motrices

REGLAS ESTRICTAS:
- Devuelve SOLO el JSON. No expliques tu razonamiento.
- No inventes información. Si un campo no está presente, usa valores por defecto (lista vacía para materiales, string vacío para tarea).
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


def _obtener_modelo_disponible(cliente, modelo_preferido: str) -> str:
    try:
        modelos = list(cliente.models.list())
    except Exception as exc:
        logger.warning("No se pudo listar los modelos disponibles: %s", exc)
        return modelo_preferido

    modelos_por_nombre = {m.name: m for m in modelos if hasattr(m, "name") and m.name}

    candidatos = [
        m for m in modelos_por_nombre.values()
        if any(metodo in (m.supported_actions or []) for metodo in ["generateContent", "generate_content"])
    ]

    if candidatos:
        return candidatos[0].name

    if modelo_preferido in modelos_por_nombre:
        return modelo_preferido

    return modelo_preferido


def procesar_documento_con_gemini(texto_crudo: str) -> dict:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY no está definida en las variables de entorno.")

    modelo_preferido = os.getenv("GEMINI_MODEL", "gemini-1.0-pro")
    cliente = genai.Client(api_key=api_key)
    modelo = _obtener_modelo_disponible(cliente, modelo_preferido)

    if modelo != modelo_preferido:
        logger.info("Usando modelo alternativo de Gemini: %s", modelo)

    prompt = PROMPT_BASE + texto_crudo
    try:
        respuesta = cliente.models.generate_content(model=modelo, contents=prompt)
        texto_respuesta = respuesta.text
    except genai_errors.ClientError as exc:
        if exc.status_code == 404:
            modelo = _obtener_modelo_disponible(cliente, modelo_preferido)
            logger.info("Reintentando con modelo alternativo tras 404: %s", modelo)
            respuesta = cliente.models.generate_content(model=modelo, contents=prompt)
            texto_respuesta = respuesta.text
        else:
            logger.exception("Error en la API de Gemini")
            raise RuntimeError(f"Error en la API de Gemini ({modelo}): {exc.message}") from exc
    except Exception as exc:
        logger.exception("Error inesperado al llamar a Gemini")
        raise RuntimeError(f"Error inesperado al llamar a Gemini: {exc}") from exc

    try:
        json_limpio = _limpiar_json_respuesta(texto_respuesta)
        datos = json.loads(json_limpio)
    except json.JSONDecodeError as exc:
        logger.exception("Gemini devolvió un JSON inválido")
        raise RuntimeError("La IA devolvió un formato inválido. Intenta con otro documento.") from exc

    return {
        "resumen_sesion": datos.get("resumen_sesion", ""),
        "tarea": datos.get("tarea", ""),
        "materiales": datos.get("materiales", []),
        "semaforo": datos.get("semaforo", "amarillo"),
        "categoria": datos.get("categoria", "cognitivo"),
    }
