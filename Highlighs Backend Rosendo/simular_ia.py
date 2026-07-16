import os
import shutil
import time

# Configuración de la carpeta donde ya está tu video
CARPETA_VIDEOS = "./highlights_media_bd"
VIDEO_ORIGINAL_RUTA = os.path.join(CARPETA_VIDEOS, "troleado.mp4")

# Verificar si el video realmente está ahí
if not os.path.exists(VIDEO_ORIGINAL_RUTA):
    print(f"❌ Error: No encontré 'troleado.mp4' dentro de '{CARPETA_VIDEOS}'.")
    print("👉 Asegúrate de que el nombre del archivo esté escrito exactamente igual.")
    exit()

ahora = time.time()
un_dia_en_segundos = 86400

# Estructura de nombres falsos de la IA
videos_falsos_ia = [
    {"nombre": "emp01_ensamblaje_20260716_143000.mp4", "antiguedad_dias": 0},  # Registro de hoy
    {"nombre": "emp02_empaque_20260715_091522.mp4", "antiguedad_dias": 1},     # Registro de ayer
    {"nombre": "emp03_inspeccion_20260714_184510.mp4", "antiguedad_dias": 2},  # Registro de hace 2 días
]

print(f"🎬 Procesando 'troleado.mp4' para generar los formatos de la IA...")

for v in videos_falsos_ia:
    ruta_destino = os.path.join(CARPETA_VIDEOS, v["nombre"])
    
    # Copiar el video dentro de la misma carpeta pero con el nuevo nombre
    shutil.copy2(VIDEO_ORIGINAL_RUTA, ruta_destino)
    
    # Modificar la fecha del archivo en Windows para que el backend lo ordene bien
    fecha_modificada = ahora - (v["antiguedad_dias"] * un_dia_en_segundos)
    os.utime(ruta_destino, (fecha_modificada, fecha_modificada))
    print(f"   -> Creado con éxito: {v['nombre']}")

# Opcional: Eliminar el molde original 'troleado.mp4' para que el backend no lo liste solo
try:
    os.remove(VIDEO_ORIGINAL_RUTA)
    print("\n🧹 Archivo 'troleado.mp4' original removido para limpiar la carpeta.")
except Exception:
    pass

print("\n🎉 ¡Listo! Tus 3 videos reales e interactivos ya están preparados.")
