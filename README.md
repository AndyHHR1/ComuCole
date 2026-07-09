# ComuCole

Plataforma de comunicación escolar entre docentes y padres potenciada por IA.

## Estructura del Proyecto

```
ComuCole/
├── backend/                 # API FastAPI
│   ├── main.py              # App principal + endpoints
│   ├── models/              # Esquemas Pydantic
│   └── services/            # Lógica de negocio (docx, gemini)
├── frontend/                # Cliente web responsivo
│   ├── index.html           # Panel del docente
│   ├── padre.html           # Panel del padre
│   ├── css/
│   └── js/
├── requirements.txt         # Dependencias Python
├── Dockerfile               # Imagen para producción (Render)
├── render.yaml              # Configuración de deploy en Render
├── .gitignore
└── .dockerignore
```

## Requisitos

- Python 3.11+
- Cuenta en [Google AI Studio](https://aistudio.google.com/) con API Key de Gemini
- Cuenta en [Render](https://render.com/)

## Desarrollo Local

```bash
# 1. Clona el repositorio
git clone <repo-url>
cd ComuCole

# 2. Crea el entorno virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 3. Instala dependencias
pip install -r requirements.txt

# 4. Configura variables de entorno
cp .env.example .env
# Edita .env y agrega tu GOOGLE_API_KEY

# 5. Levanta el servidor
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Accede a:
- **Panel Docente**: `http://localhost:8000/` (arrastra el .docx)
- **Panel Padre**: `http://localhost:8000/padre.html`
- **API Docs**: `http://localhost:8000/docs`

## Deploy en Render (Docker)

### Opción 1: Usando `render.yaml`

1. Sube este repositorio a GitHub/GitLab.
2. Crea un nuevo **Web Service** en Render.
3. Conecta tu repositorio.
4. Render detectará automáticamente el archivo `render.yaml` y configurará:
   - Entorno: Docker
   - Región: Oregon (ajustable)
   - Health check: `/health`
   - Puerto: 8000

5. En la sección **Environment Variables** del servicio, agrega:
   - `GOOGLE_API_KEY`: tu API key de Google AI Studio
   - Marca como **Private**

6. Haz clic en **Create Web Service**.

### Opción 2: Configuración Manual

1. Crea un nuevo **Web Service** en Render.
2. Conecta tu repositorio.
3. Configuración:
   - **Environment**: `Docker`
   - **Dockerfile Path**: `./Dockerfile`
   - **Health Check Path**: `/health`
4. Variables de entorno:
   - `GOOGLE_API_KEY` (privada)

### Comandos Útiles

```bash
# Construir imagen localmente para pruebas
docker build -t comucole .

# Ejecutar contenedor localmente
docker run -p 8000:8000 -e GOOGLE_API_KEY=tu_key comucole
```

## Endpoints Principales

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/procesar-docx` | Procesa un .docx y devuelve JSON estructurado |
| `POST` | `/marcar-revisada` | Marca tarea como revisada (+1 punto) |
| `POST` | `/marcar-cumplida` | Marca tarea como cumplida (+2 puntos) |
| `GET` | `/ranking` | Obtiene tabla de posiciones |

## Variables de Entorno

| Variable | Descripción | Requerida |
|----------|-------------|-----------|
| `GOOGLE_API_KEY` | API Key de Google AI Studio (Gemini) | Sí |
| `PYTHONUNBUFFERED` | Salida de logs sin buffer en Docker | No |

## Notas

- El frontend se sirve estáticamente desde FastAPI (`StaticFiles`).
- El almacenamiento de ranking es **en memoria** (no persistente entre reinicios). Para producción, reemplazar por base de datos.
- En desarrollo local, usa `uvicorn`. En producción (Render/Docker), usa `gunicorn + uvicorn workers`.

## Licencia

MIT
