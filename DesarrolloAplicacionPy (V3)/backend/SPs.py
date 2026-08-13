import os
import datetime
from backend.db_config import obtener_cliente_turso

VIDEOS_DIR = "./data/highlights_media_bd"

# 🔄 MODIFICADO: Agregamos 'async' y 'await' a las operaciones centrales
async def crear_empleado(id_emp: int, nombre: str, genero: str, rendimiento: float, estado: str, url_imagen: str, rol_id: int, usuario_actual_id: int):
    client = obtener_cliente_turso()
    try:
        query = """
            INSERT INTO empleado (id, nombre, genero, rendimiento, estado, urlImagen, rol_id)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        await client.execute(query, [id_emp, nombre, genero, rendimiento, estado, url_imagen, rol_id])
        print(f"✅ [Turso] Empleado '{nombre}' indexado con éxito.")
    finally:
        await client.close()

async def borrar_empleado(id_emp: int, usuario_actual_id: int):
    client = obtener_cliente_turso()
    try:
        await client.execute("DELETE FROM empleado WHERE id = ?;", [id_emp])
        print(f"✅ [Turso] Registro ID {id_emp} removido físicamente.")
    finally:
        await client.close()

async def obtener_todos_los_empleados():
    client = obtener_cliente_turso()
    try:
        resultado = await client.execute("SELECT id, nombre, genero, rendimiento, estado FROM empleado;")
        columnas = ["id", "nombre", "genero", "rendimiento", "estado"]
        return [dict(zip(columnas, fila)) for fila in resultado.rows]
    finally:
        await client.close()

async def guardar_alerta(grado: str, incumplimiento: str, empleado_id: int):
    fecha_y_hora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    client = obtener_cliente_turso()
    try:
        await client.execute(
            "INSERT INTO alerta (grado, incumplimiento, fechaYHora, empleado_id) VALUES (?, ?, ?, ?);",
            [grado, incumplimiento, fecha_y_hora, empleado_id]
        )
        print(f"⚠️ Alerta guardada remotamente para empleado ID {empleado_id}")
    finally:
        await client.close()

async def obtener_todas_las_alertas():
    client = obtener_cliente_turso()
    try:
        query = """
            SELECT a.id, a.grado, a.incumplimiento, a.fechaYHora, e.nombre 
            FROM alerta a INNER JOIN empleado e ON a.empleado_id = e.id ORDER BY a.id DESC;
        """
        resultado = await client.execute(query)
        columnas = ["id", "grado", "incumplimiento", "fechaYHora", "empleado"]
        return [dict(zip(columnas, fila)) for fila in resultado.rows]
    finally:
        await client.close()

# Las funciones de parseo de metadatos de video se mantienen normales (síncronas)
def obtener_metadatos_video(nombre_archivo: str) -> dict:
    ruta_completa = os.path.join(VIDEOS_DIR, nombre_archivo)
    timestamp_creacion = os.path.getmtime(ruta_completa)
    fecha_creacion = datetime.datetime.fromtimestamp(timestamp_creacion)
    partes = nombre_archivo.replace(".mp4", "").split("_")
    
    empleado = partes[0] if len(partes) > 0 else "Desconocido"
    actividad = partes[1] if len(partes) > 1 else "Actividad Detectada"
    
    if len(partes) >= 4:
        try: fecha_creacion = datetime.datetime.strptime(f"{partes[2]}_{partes[3]}", "%Y%m%d_%H%M%S")
        except ValueError: pass

    return {
        "archivo": nombre_archivo,
        "empleado": empleado,
        "actividad": actividad,
        "fecha": fecha_creacion.strftime("%Y-%m-%d"),
        "hora": fecha_creacion.strftime("%H:%M:%S"),
        "timestamp": timestamp_creacion,
        "url_reproduccion": f"http://localhost:8000/static/videos/{nombre_archivo}"
    }

def listar_highlights_totales():
    if not os.path.exists(VIDEOS_DIR): return []
    lista = []
    for archivo in os.listdir(VIDEOS_DIR):
        if archivo.endswith((".mp4", ".avi", ".mkv")):
            try: lista.append(obtener_metadatos_video(archivo))
            except Exception: continue
    lista.sort(key=lambda x: x["timestamp"], reverse=True)
    return lista
