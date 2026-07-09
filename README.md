# ComuCole

Plataforma de comunicación escolar entre docentes y padres potenciada por IA.

## Funcionalidades

- **Procesamiento de documentos con IA**: Subí un `.docx` y Gemini extrae resumen de sesión, tarea para casa, materiales, semáforo de tiempo y categoría.
- **Publicación por sección**: El docente publica tareas filtrando por año, sección y color de aula. Todos los padres de esa sección la reciben en su perfil.
- **Perfil del padre**: Muestra la clase del día, tarea, materiales, semáforo y categoría. Incluye botones para marcar "Revisada" (+1 punto) y "Cumplida" (+2 puntos).
- **Ranking de padres**: Tabla de posiciones por puntos, actualizada en tiempo real.
- **Actualización automática**: El perfil del padre consulta cada 15 segundos si hay nuevas publicaciones.

## Estructura del Proyecto

```
ComuCole/
├── backend/                 # API FastAPI + SQLAlchemy
│   ├── main.py              # App principal + endpoints + migraciones
│   ├── config.py            # Configuración centralizada
│   ├── models/              # Modelos ORM (User, Task) + schemas Pydantic
│   ├── services/            # Lógica de negocio (docx, gemini, auth)
│   ├── database/            # Sesión SQLAlchemy
│   └── prompts/             # Prompts externos para Gemini
├── frontend/                # Cliente web responsivo (SPA)
│   ├── index.html           # Login principal (selección de rol)
│   ├── docente.html         # Panel del docente
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

- Python 3.10+
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
PYTHONPATH=/home/andyh/ComuCole uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Accede a:
- **Login**: `http://localhost:8000/` (selección de rol)
- **Panel Docente**: `http://localhost:8000/docente.html`
- **Panel Padre**: `http://localhost:8000/padre.html`
- **API Docs**: `http://localhost:8000/docs`

## Deploy en Render (Docker + PostgreSQL)

### Opción 1: Usando `render.yaml`

1. Sube este repositorio a GitHub/GitLab.
2. Crea un nuevo **Web Service** en Render.
3. Conecta tu repositorio.
4. Render detectará automáticamente el archivo `render.yaml` y configurará:
   - Entorno: Docker
   - Base de datos PostgreSQL incluida
   - Región: Oregon (ajustable)
   - Health check: `/health`
   - Puerto: 8000

5. En la sección **Environment Variables** del servicio, agrega:
   - `GOOGLE_API_KEY`: tu API key de Google AI Studio
   - Marca como **Private**
   - `GEMINI_MODEL`: opcional. Default: `gemini-1.0-pro`. Si tu API key soporta `gemini-1.5-flash`, podés cambiarlo.

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
   - `GEMINI_MODEL` (opcional). Default: `gemini-1.0-pro`

### Comandos Útiles

```bash
# Construir imagen localmente para pruebas
docker build -t comucole .

# Ejecutar contenedor localmente
docker run -p 8000:8000 -e GOOGLE_API_KEY=tu_key -e GEMINI_MODEL=gemini-1.0-pro comucole
```

## Endpoints Principales

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/me` | Obtiene perfil del usuario autenticado |
| `POST` | `/register` | Registro de usuario (docente/padre) |
| `POST` | `/login` | Autenticación JWT |
| `POST` | `/procesar-docx` | Procesa un `.docx` y devuelve JSON estructurado |
| `POST` | `/tasks` | Publica una tarea (solo docente) |
| `GET` | `/teacher/tasks` | Lista tareas del docente autenticado |
| `GET` | `/me/tasks` | Lista tareas del padre filtradas por su sección |
| `POST` | `/marcar-revisada` | Marca tarea como revisada (+1 punto) |
| `POST` | `/marcar-cumplida` | Marca tarea como cumplida (+2 puntos) |
| `GET` | `/ranking` | Obtiene tabla de posiciones |

## Variables de Entorno

| Variable | Descripción | Requerida |
|----------|-------------|-----------|
| `GOOGLE_API_KEY` | API Key de Google AI Studio (Gemini) | Sí |
| `GEMINI_MODEL` | Modelo de Gemini a usar. Default: `gemini-1.0-pro` | No |
| `PYTHONUNBUFFERED` | Salida de logs sin buffer en Docker | No |
| `DATABASE_URL` | Cadena de conexión a PostgreSQL (Render la provee) | Producción |

## Notas Técnicas

- **Frontend**: HTML/JS vanilla, servido como archivos estáticos por FastAPI (`StaticFiles`).
- **Autenticación**: JWT con `python-jose` + `bcrypt`.
- **Base de datos**: SQLAlchemy ORM. En desarrollo usa SQLite; en producción usa PostgreSQL (Render).
- **Migraciones**: Las columnas de `año`, `seccion`, `color_aula`, `categoria`, `semaforo` y `materiales` se agregan automáticamente al iniciar la app.
- **Filtrado de tareas**: El endpoint `/me/tasks` filtra por `año + seccion + color_aula` del padre. Si el padre no tiene esos datos, se muestran todas las tareas disponibles.
- **Actualizaciones en tiempo real**: El panel del padre consulta `/me/tasks` cada 15 segundos para detectar nuevas publicaciones.
- **En desarrollo local**, usá `uvicorn --reload`. **En producción** (Render/Docker), usá `gunicorn + uvicorn workers`.

## Licencia

MIT
