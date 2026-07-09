from pathlib import Path

# Rutas
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"
PROMPTS_DIR = BASE_DIR / "prompts"

# Archivos
GEMINI_PROMPT_FILE = PROMPTS_DIR / "gemini_prompt.txt"

# Gemini
GEMINI_MODEL = "gemini-1.0-pro"
GEMINI_MAX_RETRIES = 3
GEMINI_RETRY_BASE_DELAY = 2  # segundos

# Regex para extracción de tarea
TAREA_REGEX_PATTERNS = [
    r"Finalmente,\s*entrego\s+una\s+hoja\s+gr[aá]fica[^.]*\.",
    r"Finalmente,\s*entrego\s+una\s+ficha[^.]*\.",
    r"Como\s+actividad\s+final[^.]*\.",
    r"Para\s+la\s+casa[^.]*\.",
    r"Tarea[^:]*:\s*[^.]+(?:\.[^.]*)?",
    r"Actividad\s+para\s+casa[^:]*:\s*[^.]+(?:\.[^.]*)?",
    r"Se\s+entrega\s+una\s+ficha/hoja\s+gr[aá]fica[^.]*\.",
]

# Validaciones
ALLOWED_DOCX_EXTENSION = ".docx"
TEMP_DIR = Path("/tmp")
