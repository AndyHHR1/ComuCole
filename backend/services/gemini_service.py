import json
import logging
import os
import re
import time
from pathlib import Path

from google import genai
from google.genai import errors as genai_errors

from backend.config import (
    GEMINI_MAX_RETRIES,
    GEMINI_MODEL,
    GEMINI_PROMPT_FILE,
    GEMINI_RETRY_BASE_DELAY,
    TAREA_REGEX_PATTERNS,
)

logger = logging.getLogger(__name__)


def _leer_prompt() -> str:
    """Lee el prompt base desde el archivo externo."""
    try:
        return GEMINI_PROMPT_FILE.read_text(encoding="utf-8")
    except Exception as exc:
        logger.exception("No se pudo leer el archivo de prompt: %s", GEMINI_PROMPT_FILE)
        raise RuntimeError(f"No se pudo cargar el prompt de Gemini: {exc}") from exc


def _limpiar_json_respuesta(texto: str) -> str:
    """Limpia markdown o fences de código alrededor del JSON."""
    texto = texto.strip()
    if texto.startswith("```"):
        texto = re.sub(r"^```(?:json)?\s*", "", texto)
        texto = re.sub(r"\s*```$", "", texto)
    return texto.strip()


def _obtener_modelo_disponible(cliente: genai.Client, modelo_preferido: str) -> str:
    """Intenta listar modelos disponibles y elige el primero compatible con generateContent."""
    try:
        modelos = list(cliente.models.list())
    except Exception as exc:
        logger.warning("No se pudo listar los modelos disponibles: %s", exc)
        return modelo_preferido

    modelos_por_nombre = {m.name: m for m in modelos if getattr(m, "name", None)}

    candidatos = [
        m for m in modelos_por_nombre.values()
        if any(metodo in (getattr(m, "supported_actions", None) or []) for metodo in ["generateContent", "generate_content"])
    ]

    if candidatos:
        return candidatos[0].name

    return modelo_preferido


def _intentar_generate_content(
    cliente: genai.Client,
    modelo: str,
    prompt: str,
    max_reintentos: int = GEMINI_MAX_RETRIES,
) -> str:
    """Llama a Gemini con reintentos y backoff exponencial para errores 429/503."""
    ultimo_error: Exception | None = None

    for intento in range(max_reintentos):
        try:
            respuesta = cliente.models.generate_content(
                model=modelo,
                contents=prompt,
            )
            return respuesta.text
        except genai_errors.ClientError as exc:
            status_code = getattr(exc, 'status_code', None)
            mensaje = getattr(exc, 'message', str(exc))
            if status_code == 404:
                raise RuntimeError(f"Modelo no disponible: {modelo}") from exc
            if status_code in (429, 503):
                espera = GEMINI_RETRY_BASE_DELAY * (2 ** intento)
                logger.warning(
                    "Error %s en Gemini. Reintento %s/%s en %ss",
                    status_code,
                    intento + 1,
                    max_reintentos,
                    espera,
                )
                time.sleep(espera)
                ultimo_error = exc
                continue
            raise RuntimeError(f"Error en la API de Gemini ({modelo}): {mensaje}") from exc
        except Exception as exc:
            raise RuntimeError(f"Error inesperado al llamar a Gemini: {exc}") from exc

    raise RuntimeError(
        "El servicio de IA está con mucha demanda en este momento. "
        "Por favor, esperá unos minutos y volvé a intentarlo."
    ) from ultimo_error


def _extraer_tarea_por_regex(texto_crudo: str) -> str:
    """Extrae la tarea desde el texto crudo usando patrones regex como fallback."""
    for patron in TAREA_REGEX_PATTERNS:
        coincidencia = re.search(patron, texto_crudo, re.IGNORECASE)
        if coincidencia:
            return coincidencia.group(0).strip()
    return ""


def procesar_documento_con_gemini(texto_crudo: str) -> dict:
    """
    Procesa el texto crudo de un documento .docx usando Gemini y devuelve
    un diccionario estructurado con resumen, tarea, materiales, semáforo y categoría.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY no está definida en las variables de entorno.")

    modelo_preferido = os.getenv("GEMINI_MODEL", GEMINI_MODEL)
    cliente = genai.Client(api_key=api_key)
    modelo = _obtener_modelo_disponible(cliente, modelo_preferido)

    if modelo != modelo_preferido:
        logger.info("Usando modelo alternativo de Gemini: %s", modelo)

    prompt = _leer_prompt() + texto_crudo
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

    tarea = datos.get("tarea", "")
    if not tarea:
        tarea = _extraer_tarea_por_regex(texto_crudo)
        if tarea:
            logger.info("Tarea extraída por regex: %s", tarea)

    return {
        "resumen_sesion": datos.get("resumen_sesion", ""),
        "tarea": tarea,
        "materiales": datos.get("materiales", []),
        "semaforo": datos.get("semaforo", "amarillo"),
        "categoria": datos.get("categoria", "cognitivo"),
    }
