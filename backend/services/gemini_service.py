import json
import logging
import os
import re
import time

from google import genai
from google.genai import errors as genai_errors

logger = logging.getLogger(__name__)

PROMPT_BASE = """Eres un asistente especializado en análisis de documentos escolares para la plataforma ComuCole.
A continuación recibirás el texto crudo extraído de un documento .docx de planificación docente.

Tu tarea es extraer ESTRICTAMENTE los siguientes bloques y devolver SOLO un JSON válido (sin markdown, sin ```json, sin texto adicional):

1. "resumen_sesion": Un resumen amigable y ejecutivo (máximo 2 párrafos). Busca una sección llamada "DESARROLLO DE LA ACTIVIDAD" o "DESARROLLO DE LAS ACTIVIDADES DE APRENDIZAJE". Dentro de esa sección, hay subapartados como "INICIO", "DESARROLLO" y "CIERRE". Resume qué hicieron los niños en la sesión, qué aprendieron y cómo trabajaron. NO digas que no hay información si ves esos subapartados.

2. "tarea": La instrucción exacta para la casa. Busca en el apartado "CIERRE". REGLAS:
   - Las preguntas de reflexión (ej: "¿Qué aprendimos hoy?", "¿Cómo descubrimos...?") NO son la tarea.
   - Frases como "Escucho sus respuestas", "retroalimento", "reforzamos ideas" NO son la tarea.
   - La tarea real suele venir DESPUÉS de eso, frecuentemente con frases como:
     * "Finalmente, entrego una hoja gráfica..."
     * "Como actividad final, ..."
     * "Para la casa: ..."
     * "Tarea: ..."
     * "Actividad para casa: ..."
     * "Se entrega una ficha/hoja gráfica..."
   - Extrae SOLO la instrucción concreta para casa.
   - Si no encuentras ninguna actividad concreta para la casa, devuelve "".

3. "materiales": Lista de útiles o recursos. Busca en secciones como "RECURSOS Y MATERIALES SUGERIDOS" o items como "Gorro mágico", "Imágenes", "Limpiatipo", "Semáforo", "Tarjetas", "Hoja gráfica", "Fichas", etc. Devuelve cada material como un item separado. Si no hay materiales, devuelve [].

4. "semaforo": Clasifica el tiempo de entrega en UNO de estos 3 strings exactos:
   - "rojo" -> Es para ya / mucha carga
   - "amarillo" -> Tienes tiempo / plazo moderado
   - "verde" -> Vas bien de tiempo / plazo amplio

5. "categoria": Clasifica el tipo de trabajo en UNO de estos 3 strings exactos:
   - "cognitivo" -> Estudio, lectura, matemática, reconocer semejanzas y diferencias, observar imágenes, comunicarse oralmente
   - "manual" -> Maquetas, arte, materiales, recortar, pegar, armar
   - "psicomotriz" -> Educación física o actividades motrices

REGLAS ESTRICTAS:
- Devuelve SOLO el JSON. No expliques tu razonamiento.
- No inventes información.
- Si no encuentras un campo, usa valores por defecto: tarea = "", materiales = [], semaforo = "amarillo", categoria = "cognitivo".
- El JSON debe ser parseable directamente con json.loads().
- Usa exactamente estas claves: resumen_sesion, tarea, materiales, semaforo, categoria.

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


def _intentar_generate_content(cliente, modelo: str, prompt: str, max_reintentos: int = 3) -> str:
    espera_base = 2
    ultimo_error = None

    for intento in range(max_reintentos):
        try:
            respuesta = cliente.models.generate_content(
                model=modelo,
                contents=prompt,
            )
            return respuesta.text
        except genai_errors.ClientError as exc:
            if exc.status_code == 404:
                raise RuntimeError(f"Modelo no disponible: {modelo}") from exc
            if exc.status_code in (429, 503):
                espera = espera_base * (2 ** intento)
                logger.warning("Error %s en Gemini. Reintento %s/%s en %ss", exc.status_code, intento + 1, max_reintentos, espera)
                time.sleep(espera)
                ultimo_error = exc
                continue
            raise RuntimeError(f"Error en la API de Gemini ({modelo}): {exc.message}") from exc
        except Exception as exc:
            raise RuntimeError(f"Error inesperado al llamar a Gemini: {exc}") from exc

    raise RuntimeError(
        "El servicio de IA está con mucha demanda en este momento. "
        "Por favor, esperá unos minutos y volvé a intentarlo."
    ) from ultimo_error


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
    logger.info("Texto crudo extraido del docx (primeros 500 caracteres): %s", texto_crudo[:500])

    texto_respuesta = _intentar_generate_content(cliente, modelo, prompt)

    logger.info("Respuesta cruda de Gemini (primeros 1000 caracteres): %s", texto_respuesta[:1000])
    try:
        json_limpio = _limpiar_json_respuesta(texto_respuesta)
        datos = json.loads(json_limpio)
        logger.info("JSON parseado por Gemini: %s", datos)
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

