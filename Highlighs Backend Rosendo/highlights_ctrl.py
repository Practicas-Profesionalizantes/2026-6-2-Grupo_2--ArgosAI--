import os
from datetime import datetime
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Query

# Configuración del enrutador de FastAPI
router = APIRouter(
    prefix="/highlights",
    tags=["Highlights"]
)

# Configura la ruta de la carpeta donde la IA guarda los videos
VIDEOS_DIR = os.getenv("HIGHLIGHTS_VIDEOS_DIR", "./highlights_media_bd")
def obtener_metadatos_video(nombre_archivo: str) -> Dict[str, Any]:
    """
    Extrae información útil del archivo de video.
    Asume un formato de nombre: empleadoID_actividad_AAAAMMDD_HHMMSS.mp4
    """
    ruta_completa = os.path.join(VIDEOS_DIR, nombre_archivo)
    timestamp_creacion = os.path.getmtime(ruta_completa)
    fecha_creacion = datetime.fromtimestamp(timestamp_creacion)

    partes = nombre_archivo.replace(".mp4", "").split("_")
    
    empleado = partes[0] if len(partes) > 0 else "Desconocido"
    actividad = partes[1] if len(partes) > 1 else "Actividad Detectada"
    
    # 🟢 MEJORA: Intenta parsear tanto la fecha como la hora directamente desde el nombre
    if len(partes) >= 4:
        try:
            fecha_creacion = datetime.strptime(f"{partes[2]}_{partes[3]}", "%Y%m%d_%H%M%S")
        except ValueError:
            pass
    elif len(partes) == 3:
        try:
            fecha_creacion = datetime.strptime(partes[2], "%Y%m%d")
        except ValueError:
            pass

    return {
        "archivo": nombre_archivo,
        "empleado": empleado,
        "actividad": actividad,
        "fecha": fecha_creacion.strftime("%Y-%m-%d"),
        "hora": fecha_creacion.strftime("%H:%M:%S"),
        "timestamp": timestamp_creacion,
        "ruta_acceso": f"/static/videos/{nombre_archivo}"
    }

@router.get("/listar", response_model=List[Dict[str, Any]])
async def listar_highlights_por_fecha(
    fecha_filtro: str = Query(None, description="Filtrar por fecha específica (AAAA-MM-DD)"),
    orden: str = Query("desc", description="Orden cronológico: 'asc' o 'desc'")
):
    """
    Escanea la carpeta de videos de la IA, extrae sus datos
    y los organiza cronológicamente.
    """
    # Verificar que la carpeta exista
    if not os.path.exists(VIDEOS_DIR):
        raise HTTPException(status_code=500, detail=f"La carpeta de videos '{VIDEOS_DIR}' no existe.")

    lista_highlights = []

    # Leer archivos de la carpeta
    for archivo in os.listdir(VIDEOS_DIR):
        if archivo.endswith((".mp4", ".avi", ".mkv")):
            try:
                datos_video = obtener_metadatos_video(archivo)
                
                # Aplicar filtro de fecha si se solicita
                if fecha_filtro and datos_video["fecha"] != fecha_filtro:
                    continue
                    
                lista_highlights.append(datos_video)
            except Exception as e:
                # Ignorar archivos corruptos o errores de lectura individuales
                continue

    # Ordenar los resultados por timestamp (fecha y hora exacta)
    reverse_order = True if orden == "desc" else False
    lista_highlights.sort(key=lambda x: x["timestamp"], reverse=reverse_order)

    return lista_highlights
