"""Servidor local de clips; expone solo la carpeta multimedia en loopback."""

import logging
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.storage import media_directory

logger = logging.getLogger(__name__)
VIDEOS_DIR = media_directory()
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="ArgosIA Media", docs_url=None, redoc_url=None, openapi_url=None)
frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://127.0.0.1:8501").strip()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin],
    allow_credentials=False,
    allow_methods=["GET", "HEAD"],
    allow_headers=["Range", "Content-Type"],
)
app.mount("/static/videos", StaticFiles(directory=str(VIDEOS_DIR), check_dir=True), name="videos")


@app.get("/health", include_in_schema=False)
async def health_check():
    return Response(status_code=204)


@app.exception_handler(Exception)
async def media_exception_handler(request: Request, exc: Exception):
    logger.warning("Falló una petición multimedia (%s).", type(exc).__name__)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "code": "MEDIA_UNAVAILABLE",
            "message": "No se pudo reproducir el archivo multimedia.",
        },
    )


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("ARGOS_MEDIA_PORT", "8000"))
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
