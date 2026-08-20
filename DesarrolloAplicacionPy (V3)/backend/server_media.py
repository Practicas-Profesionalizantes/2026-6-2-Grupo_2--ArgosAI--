import os
import sys
import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ============================================================
# INYECTOR DE RUTAS DINÁMICO
# ============================================================
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from backend.db_config import obtener_cliente_turso  # Valida que cargue la configuración base

# Configuración estricta del Pilar de Registros (Logging)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

app = FastAPI(title="Servidor de Medios Analíticos Seguros - ArgosIA")

# 🟢 PILAR SEGURIDAD: Control de acceso restrictivo CORS basado en variables de entorno
frontend_url = os.getenv("FRONTEND_ORIGIN", "http://localhost:8501")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url.strip()],  # Bloqueamos el acceso únicamente al puerto de tu Streamlit
    allow_credentials=True,
    allow_methods=["GET"],                 # El visualizador solo requiere peticiones de lectura de video
    allow_headers=["*"],
)

# Carga dinámica del directorio de grabaciones desde el entorno (.env)
videos_dir_raw = os.getenv("MEDIA_DIR", "./data/highlights_media_bd")
VIDEOS_DIR = Path(videos_dir_raw).resolve()

# Aseguramos de forma defensiva la existencia de la carpeta de biometría y grabaciones
os.makedirs(VIDEOS_DIR, exist_ok=True)

# Servimos de forma asíncrona la carpeta de videos como estáticos
app.mount("/static/videos", StaticFiles(directory=str(VIDEOS_DIR)), name="videos")
logging.info(f"Ruta física de grabaciones montada de forma estática en: {VIDEOS_DIR}")

# ============================================================
# 🟢 PILAR MANEJO DE ERRORES: Manejador Universal de Excepciones
# ============================================================
@app.exception_handler(Exception)
async def universal_exception_handler(request: Request, exc: Exception):
    """
    Captura cualquier falla del sistema de archivos, desbordamiento o error de ruta
    y devuelve una estructura JSON uniforme en lugar de tumbar el servicio.
    """
    logging.error(f"Falla detectada en la petición multimedia {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "code": "SERVER_MULTIMEDIA_ERROR",
            "message": "Ocurrió una falla interna en el procesamiento de video o acceso al recurso.",
            "details": str(exc) if os.getenv("DEBUG") == "True" else "Ocultado en entorno de producción"
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    # Carga de host y puertos dinámicos desde variables de entorno
    host_env = os.getenv("MEDIA_HOST", "0.0.0.0")
    port_env = int(os.getenv("MEDIA_PORT", "8000"))
    
    logging.info(f"Iniciando ciclo de vida del microservicio de video asíncrono en {host_env}:{port_env}...")
    uvicorn.run(app, host=host_env, port=port_env)
