from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import highlights_ctrl
import os

app = FastAPI(title="Backend de Monitoreo con IA")

# Asegurar que la carpeta de videos exista
os.makedirs(highlights_ctrl.VIDEOS_DIR, exist_ok=True)

# Servir los videos como archivos estáticos para que el frontend pueda reproducirlos
app.mount("/static/videos", StaticFiles(directory=highlights_ctrl.VIDEOS_DIR), name="videos")

# 🔴 CORRECCIÓN: Se debe usar el prefijo del módulo importado
app.include_router(highlights_ctrl.router)

if __name__ == "__main__":
    import uvicorn
    # Cambiado a 'py' implícito si ejecutas desde archivo, 
    # pero uvicorn directo funciona aquí si se levanta el script.
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)