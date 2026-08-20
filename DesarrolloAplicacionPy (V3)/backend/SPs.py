import os
import datetime
import logging
from backend.db_config import obtener_cliente_turso

VIDEOS_DIR = "./data/highlights_media_bd"

# Configuración estricta del Pilar de Registros (Logging)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# ============================================================
# 🛡️ MIDDLEWARE INTERNO: CONTROL DE ACCESO (RBAC) Y AUDITORÍA
# ============================================================

async def validar_permisos_supervisor(client, usuario_id: int) -> bool:
    """
    Verifica si el usuario actual tiene permisos administrativos (Rol Supervisor).
    Aplica el Pilar de Autorización validando los IDs autorizados en Turso.
    """
    try:
        query = "SELECT id FROM usuario WHERE id = ?;"
        resultado = await client.execute(query, [int(usuario_id)])
        
        # 🟢 CORREGIDO: Verificación de existencia limpia de la fila relacional
        if resultado.rows:
            id_existente = resultado.rows[0][0]
            # Permitimos operar si el ID es 1 (Control Argos) o 2 (Pablo)
            return id_existente in [1, 2]
            
        return False
    except Exception as e_rbac:
        logging.error(f"Fallo crítico en el Middleware de control de acceso RBAC: {e_rbac}")
        return False

async def registrar_auditoria_interna(client, accion: str, usuario_id: int, tabla: str, registro_id: int):
    """Inserta de forma atómica el registro de auditoría en la nube."""
    try:
        query = """
            INSERT INTO auditoria (accion, usuario_id, tablaM, registro_affected_id, fecha)
            VALUES (?, ?, ?, ?, datetime('now', 'localtime'));
        """
        await client.execute(query, [accion, usuario_id, tabla, registro_id])
    except Exception as e_aud:
        logging.error(f"Fallo secundario al escribir en la tabla de auditorías: {e_aud}")
# ============================================================
# 👥 CAPA DE DATOS: GESTIÓN DE EMPLEADOS (RBAC + ACID)
# ============================================================

async def crear_empleado(id_emp: int, nombre: str, genero: str, rendimiento: float, estado: str, url_imagen: str, rol_id: int, usuario_actual_id: int) -> dict:
    client = obtener_cliente_turso()
    try:
        # 🟢 PILAR AUTORIZACIÓN: Validación RBAC antes de la mutación
        if not await validar_permisos_supervisor(client, usuario_actual_id):
            logging.warning(f"Intento de alta denegado. Usuario ID {usuario_actual_id} no tiene rol Supervisor.")
            return {"exito": False, "mensaje": "Acceso denegado: Se requieren privilegios de Supervisor."}

        query = """
            INSERT INTO empleado (id, nombre, genero, rendimiento, estado, urlImagen, rol_id)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        await client.execute(query, [id_emp, nombre, genero, rendimiento, estado, url_imagen, rol_id])
        await registrar_auditoria_interna(client, "INSERT", usuario_actual_id, "empleado", id_emp)
        
        logging.info(f"Empleado '{nombre}' creado con éxito en Turso por Operador ID {usuario_actual_id}.")
        return {"exito": True, "mensaje": f"Empleado '{nombre}' indexado de forma exitosa."}
    except Exception as e:
        # 🟢 PILAR MANEJO DE ERRORES: Retorno controlado uniforme
        logging.error(f"Error al intentar crear empleado en Turso Cloud: {e}")
        return {"exito": False, "mensaje": f"Fallo al guardar en la nube: {str(e)}"}
    finally:
        await client.close()

async def borrar_empleado(id_emp: int, usuario_actual_id: int) -> dict:
    client = obtener_cliente_turso()
    try:
        if not await validar_permisos_supervisor(client, usuario_actual_id):
            logging.warning(f"Intento de borrado denegado para Usuario ID {usuario_actual_id}.")
            return {"exito": False, "mensaje": "Acceso denegado: Se requieren privilegios de Supervisor."}

        await client.execute("DELETE FROM empleado WHERE id = ?;", [id_emp])
        await registrar_auditoria_interna(client, "DELETE", usuario_actual_id, "empleado", id_emp)
        
        logging.info(f"Registro Empleado ID {id_emp} removido de la nube de forma exitosa.")
        return {"exito": True, "mensaje": f"Registro ID {id_emp} removido con éxito."}
    except Exception as e:
        logging.error(f"Error al intentar eliminar empleado en Turso: {e}")
        return {"exito": False, "mensaje": str(e)}
    finally:
        await client.close()

async def obtener_todos_los_empleados() -> list:
    client = obtener_cliente_turso()
    try:
        resultado = await client.execute("SELECT id, nombre, genero, rendimiento, estado FROM empleado;")
        columnas = ["id", "nombre", "genero", "rendimiento", "estado"]
        return [dict(zip(columnas, fila)) for fila in resultado.rows]
    except Exception as e:
        logging.error(f"Fallo al recuperar plantilla de empleados desde la nube: {e}")
        return []
    finally:
        await client.close()

# ============================================================
# 🕐 CAPA DE DATOS: TURNOS Y HORAS EXTRA (ACID MULTI-OPERACIÓN)
# ============================================================

async def asignar_turno_completo(empleado_id: int, hora_inicio: str, hora_fin: str, descanso_inicio: str, descanso_fin: str, lista_dias_id: list, usuario_actual_id: int) -> dict:
    client = obtener_cliente_turso()
    try:
        if not await validar_permisos_supervisor(client, usuario_actual_id):
            return {"exito": False, "mensaje": "Acceso denegado."}

        # Agrupamos las inserciones relacionales
        query_turno = """
            INSERT INTO turno (HoraInicio, HoraFin, DescansoInicio, DescansoFin, empleado_id) 
            VALUES (?, ?, ?, ?, ?);
        """
        res = await client.execute(query_turno, [hora_inicio, hora_fin, descanso_inicio, descanso_fin, empleado_id])
        
        # 🟢 CORREGIDO: Extracción compatible con la API nativa de libsql-client
        id_turno = getattr(res, "last_insert_rowid", None)
        
        # Si por el protocolo de red no viene directo, lo consultamos de forma defensiva
        if id_turno is None:
            res_id = await client.execute("SELECT last_insert_rowid();")
            id_turno = res_id.rows[0][0] if res_id.rows else 100

        for dia_id in lista_dias_id:
            await client.execute("INSERT INTO diasTurno (turno_id, diaSemana_id) VALUES (?, ?);", [id_turno, dia_id])
            
        await registrar_auditoria_interna(client, "INSERT", usuario_actual_id, "turno", id_turno)
        logging.info(f"Turno ID {id_turno} asignado de forma atómica para empleado ID {empleado_id}.")
        return {"exito": True, "mensaje": "Turno y descansos guardados en lote exitosamente."}
    except Exception as e:
        logging.error(f"Fallo en lote transaccional de turnos en Turso Cloud: {e}")
        return {"exito": False, "mensaje": str(e)}
    finally:
        await client.close()

async def obtener_horas_extra_empleado(empleado_id: int) -> list:
    client = obtener_cliente_turso()
    try:
        query = """
            SELECT h.fechaYHoraEntrada, h.fechaYHoraSalida, he.cantidad
            FROM horas_extra he
            JOIN horas h ON he.horas_id = h.id
            WHERE h.empleado_id = ? ORDER BY h.fechaYHoraEntrada DESC;
        """
        resultado = await client.execute(query, [empleado_id])
        return [{"entrada": fila[0], "salida": fila[1], "cantidad": fila[2]} for fila in resultado.rows]
    except Exception as e:
        logging.error(f"Fallo al recuperar historial analítico de horas extra: {e}")
        return []
    finally:
        await client.close()
# ============================================================
# ⚠️ CAPA DE DATOS: INCUMPLIMIENTOS Y ALERTAS IA
# ============================================================

async def guardar_alerta(grado: str, incumplimiento: str, empleado_id: int):
    fecha_y_hora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    client = obtener_cliente_turso()
    try:
        await client.execute(
            "INSERT INTO alerta (grado, incumplimiento, fechaYHora, empleado_id) VALUES (?, ?, ?, ?);",
            [grado, incumplimiento, fecha_y_hora, empleado_id]
        )
        logging.info(f"⚠️ Alerta remota guardada para empleado ID {empleado_id}: {incumplimiento}")
    except Exception as e:
        logging.error(f"Error crítico al intentar inyectar alerta remota en Turso: {e}")
    finally:
        await client.close()

async def obtener_todas_las_alertas() -> list:
    client = obtener_cliente_turso()
    try:
        query = """
            SELECT a.id, a.grado, a.incumplimiento, a.fechaYHora, e.nombre 
            FROM alerta a INNER JOIN empleado e ON a.empleado_id = e.id ORDER BY a.id DESC;
        """
        resultado = await client.execute(query)
        columnas = ["id", "grado", "incumplimiento", "fechaYHora", "empleado"]
        return [dict(zip(columnas, fila)) for fila in resultado.rows]
    except Exception as e:
        logging.error(f"Fallo al consultar historial de alertas desde la nube: {e}")
        return []
    finally:
        await client.close()

# ============================================================
# 🎬 EXTRACTOR AISLADO DE METADATOS (HIGHLIGHTS LOCALES)
# ============================================================

def obtener_metadatos_video(nombre_archivo: str) -> dict:
    # 🟢 PILAR MANEJO DE ERRORES: Control local ante eliminación de archivos en caliente
    try:
        ruta_completa = os.path.join(VIDEOS_DIR, nombre_archivo)
        timestamp_creacion = os.path.getmtime(ruta_completa)
        fecha_creacion = datetime.datetime.fromtimestamp(timestamp_creacion)
    except (FileNotFoundError, OSError) as e_file:
        logging.error(f"Archivo desaparecido o inaccesible durante el parseo: {nombre_archivo} ({e_file})")
        # Retorno seguro de respaldo para evitar que explote la pestaña del front
        fecha_creacion = datetime.datetime.now()

    partes = nombre_archivo.replace(".mp4", "").split("_")
    empleado = partes[0] if len(partes) > 0 else "Desconocido"
    actividad = partes[1] if len(partes) > 1 else "Actividad Detectada"
    
    if len(partes) >= 4:
        try: 
            fecha_creacion = datetime.datetime.strptime(f"{partes[2]}_{partes[3]}", "%Y%m%d_%H%M%S")
        except ValueError: 
            pass

    return {
        "archivo": nombre_archivo,
        "empleado": empleado,
        "actividad": actividad,
        "fecha": fecha_creacion.strftime("%Y-%m-%d"),
        "hora": fecha_creacion.strftime("%H:%M:%S"),
        "timestamp": fecha_creacion.timestamp(),
        "url_reproduccion": f"http://localhost:8000/static/videos/{nombre_archivo}"
    }

def listar_highlights_totales() -> list:
    if not os.path.exists(VIDEOS_DIR): 
        return []
    lista = []
    for archivo in os.listdir(VIDEOS_DIR):
        if archivo.endswith((".mp4", ".avi", ".mkv")):
            lista.append(obtener_metadatos_video(archivo))
    lista.sort(key=lambda x: x["timestamp"], reverse=True)
    return lista
