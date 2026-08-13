from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="Servidor de Medios de Video - ArgosIA")

# Habilitamos CORS para que Streamlit pueda llamar libremente a los videos sin bloqueos
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

VIDEOS_DIR = "./data/highlights_media_bd"
os.makedirs(VIDEOS_DIR, exist_ok=True)

# Servimos de forma estática la carpeta multimedia
app.mount("/static/videos", StaticFiles(directory=VIDEOS_DIR), name="videos")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
