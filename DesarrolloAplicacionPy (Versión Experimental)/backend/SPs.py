import datetime
import logging
import os
from backend.db_config import obtener_cliente_turso

VIDEOS_DIR = "./data/highlights_media_bd"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


# ============================================================
# 🛡️ MIDDLEWARE INTERNO: CONTROL DE ACCESO (RBAC) Y AUDITORÍA
# ============================================================


async def validar_permisos_supervisor(client, usuario_id: int) -> bool:
  """Verifica si el usuario actual tiene permisos administrativos (Rol Supervisor)."""
  try:
    query = "SELECT id FROM usuario WHERE id = ?;"
    resultado = await client.execute(query, [int(usuario_id)])
    if resultado.rows:
      id_existente = resultado.rows[0][0]
      return id_existente in [1, 2]
    return False
  except Exception as e_rbac:
    logging.error(f"Fallo en RBAC: {e_rbac}")
    return False


async def registrar_auditoria_interna(
    client, accion: str, usuario_id: int, tabla: str, registro_id: int
):
  """Inserta el registro de auditoría en Turso."""
  try:
    query = """
            INSERT INTO auditoria (accion, usuario_id, tablaM, registro_affected_id, fecha)
            VALUES (?, ?, ?, ?, datetime('now', 'localtime'));
        """
    await client.execute(query, [accion, usuario_id, tabla, registro_id])
  except Exception as e_aud:
    logging.error(f"Fallo en auditoría: {e_aud}")


# ============================================================
# 👥 CAPA DE DATOS: GESTIÓN DE EMPLEADOS
# ============================================================


async def crear_empleado(
    id_emp: int,
    nombre: str,
    genero: str,
    rendimiento: float,
    estado: str,
    url_imagen: str,
    rol_id: int,
    usuario_actual_id: int,
) -> dict:
  """Crea un nuevo empleado con validación RBAC y registro de auditoría."""
  client = obtener_cliente_turso()
  try:
    if not await validar_permisos_supervisor(client, usuario_actual_id):
      return {
          "exito": False,
          "mensaje": (
              "Acceso denegado: Se requieren privilegios de Supervisor."
          ),
      }

    query = """
            INSERT INTO empleado (id, nombre, genero, rendimiento, estado, urlImagen, rol_id)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """
    await client.execute(
        query,
        [id_emp, nombre, genero, rendimiento, estado, url_imagen, rol_id],
    )
    await registrar_auditoria_interna(
        client, "INSERT", usuario_actual_id, "empleado", id_emp
    )
    return {"exito": True, "mensaje": f"Empleado '{nombre}' creado con éxito."}
  except Exception as e:
    logging.error(f"Error al crear empleado: {e}")
    return {"exito": False, "mensaje": f"Fallo al guardar en la nube: {str(e)}"}
  finally:
    await client.close()


async def borrar_empleado(id_emp: int, usuario_actual_id: int) -> dict:
  """Elimina un empleado por ID con validación RBAC."""
  client = obtener_cliente_turso()
  try:
    if not await validar_permisos_supervisor(client, usuario_actual_id):
      return {
          "exito": False,
          "mensaje": (
              "Acceso denegado: Se requieren privilegios de Supervisor."
          ),
      }

    await client.execute("DELETE FROM empleado WHERE id = ?;", [id_emp])
    await registrar_auditoria_interna(
        client, "DELETE", usuario_actual_id, "empleado", id_emp
    )
    return {"exito": True, "mensaje": f"Registro ID {id_emp} eliminado."}
  except Exception as e:
    logging.error(f"Error al eliminar empleado: {e}")
    return {"exito": False, "mensaje": str(e)}
  finally:
    await client.close()


async def obtener_todos_los_empleados() -> list:
  """Recupera el listado completo de empleados como diccionarios."""
  client = obtener_cliente_turso()
  try:
    resultado = await client.execute(
        "SELECT id, nombre, genero, rendimiento, estado FROM empleado;"
    )
    columnas = ["id", "nombre", "genero", "rendimiento", "estado"]
    return [dict(zip(columnas, fila)) for fila in resultado.rows]
  except Exception as e:
    logging.error(f"Fallo al recuperar empleados: {e}")
    return []
  finally:
    await client.close()


# ============================================================
# 🕐 CAPA DE DATOS: TURNOS Y HORAS EXTRA
# ============================================================


async def asignar_turno_completo(
    empleado_id: int,
    hora_inicio: str,
    hora_fin: str,
    descanso_inicio: str,
    descanso_fin: str,
    lista_dias_id: list,
    usuario_actual_id: int,
) -> dict:
  """Asigna un turno con sus días asociados a un empleado."""
  client = obtener_cliente_turso()
  try:
    if not await validar_permisos_supervisor(client, usuario_actual_id):
      return {"exito": False, "mensaje": "Acceso denegado."}

    query_turno = """
            INSERT INTO turno (HoraInicio, HoraFin, DescansoInicio, DescansoFin, empleado_id) 
            VALUES (?, ?, ?, ?, ?);
        """
    res = await client.execute(
        query_turno,
        [hora_inicio, hora_fin, descanso_inicio, descanso_fin, empleado_id],
    )

    id_turno = getattr(res, "last_insert_rowid", None)
    if id_turno is None:
      res_id = await client.execute("SELECT last_insert_rowid();")
      id_turno = res_id.rows[0][0] if res_id.rows else 1

    for dia_id in lista_dias_id:
      await client.execute(
          "INSERT INTO diasTurno (turno_id, diaSemana_id) VALUES (?, ?);",
          [id_turno, dia_id],
      )

    await registrar_auditoria_interna(
        client, "INSERT", usuario_actual_id, "turno", id_turno
    )
    return {"exito": True, "mensaje": "Turno asignado exitosamente."}
  except Exception as e:
    logging.error(f"Fallo en asignación de turno: {e}")
    return {"exito": False, "mensaje": str(e)}
  finally:
    await client.close()


async def obtener_horas_extra_empleado(empleado_id: int) -> list:
  """Consulta las horas extra registradas para un empleado."""
  client = obtener_cliente_turso()
  try:
    query = """
            SELECT h.fechaYHoraEntrada, h.fechaYHoraSalida, he.cantidad
            FROM horas_extra he
            JOIN horas h ON he.horas_id = h.id
            WHERE h.empleado_id = ? ORDER BY h.fechaYHoraEntrada DESC;
        """
    resultado = await client.execute(query, [empleado_id])
    return [
        {"entrada": fila[0], "salida": fila[1], "cantidad": fila[2]}
        for fila in resultado.rows
    ]
  except Exception as e:
    logging.error(f"Fallo al recuperar horas extra: {e}")
    return []
  finally:
    await client.close()


# ============================================================
# ⚠️ CAPA DE DATOS: INCUMPLIMIENTOS Y ALERTAS (VIDEO OPCIONAL)
# ============================================================


async def guardar_alerta(
    grado: str,
    incumplimiento: str,
    empleado_id: int,
    url_video: str | None = None,
):
  """Guarda una alerta en la BD.

  La URL del video es opcional.
  """
  fecha_y_hora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  async with obtener_cliente_turso() as client:
    try:
      query = """
                INSERT INTO alerta (grado, incumplimiento, fechaYHora, empleado_id, url_video) 
                VALUES (?, ?, ?, ?, ?);
            """
      await client.execute(
          query, [grado, incumplimiento, fecha_y_hora, empleado_id, url_video]
      )
      logging.info(f"Alerta registrada para empleado ID {empleado_id}")
      return {"exito": True, "mensaje": "Alerta guardada con éxito."}
    except Exception as e:
      logging.error(f"Error al guardar alerta: {e}")
      raise e


async def obtener_todas_las_alertas() -> list:
  """Recupera todas las alertas con la información de empleado y URL de video (VERSIÓN DIAGNÓSTICO)."""
  client = obtener_cliente_turso()
  try:
    query = """
            SELECT a.id, a.grado, a.incumplimiento, a.fechaYHora, 
                   COALESCE(e.nombre, 'Sistema / Desconocido') AS empleado,
                   a.url_video
            FROM alerta a 
            LEFT JOIN empleado e ON a.empleado_id = e.id 
            ORDER BY a.id DESC;
        """
    resultado = await client.execute(query)

    # 🔍 PRINT DE DIAGNÓSTICO
    print("\n" + "=" * 50)
    print(">>> TIPO DE OBJETO DEVUELTO POR TURSO:", type(resultado))
    print(">>> CONTENIDO DE RESULTADO:", repr(resultado))
    if hasattr(resultado, "rows"):
      print(">>> FILAS EN RESULTADO.ROWS:", resultado.rows)
    print("=" * 50 + "\n")

    filas = getattr(resultado, "rows", [])
    columnas = [
        "id",
        "grado",
        "incumplimiento",
        "fechaYHora",
        "empleado",
        "url_video",
    ]
    return [dict(zip(columnas, fila)) for fila in filas]
  except Exception as e:
    logging.error(f"Fallo al consultar alertas: {e}")
    # 🔍 PRINT EN CASO DE ERROR DENTRO DEL TRY/EXCEPT
    import traceback

    print("\n" + "!" * 50)
    print(">>> TRACEBACK COMPLETO DEL ERROR EN ALERTAS:")
    traceback.print_exc()
    print("!" * 50 + "\n")
    return []
  finally:
    await client.close()


async def obtener_incumplimientos_seguridad() -> list:
  """Alias para mantener retrocompatibilidad."""
  return await obtener_todas_las_alertas()

# ============================================================
# 📊 CAPA DE DATOS: RENDIMIENTO Y JORNADAS REALES
# ============================================================


async def obtener_rendimiento_y_jornada():
  """Obtiene las métricas de desempeño y horarios desde Turso."""
  client = obtener_cliente_turso()
  try:
    res_emp = await client.execute("""
            SELECT e.id, e.nombre, COALESCE(r.nombreRol, 'Sin Rol') AS rol, e.rendimiento, e.estado 
            FROM empleado e 
            LEFT JOIN rol_empleado r ON e.rol_id = r.id;
        """)
    res_jornada = await client.execute("""
            SELECT e.nombre AS empleado, 
                   COALESCE(t.HoraInicio, 'N/A') AS hora_inicio, 
                   COALESCE(t.HoraFin, 'N/A') AS hora_fin, 
                   COALESCE(h.fechaYHoraEntrada, 'Sin registro') AS entrada, 
                   COALESCE(h.fechaYHoraSalida, 'Sin registro') AS salida
            FROM empleado e
            LEFT JOIN turno t ON e.id = t.empleado_id
            LEFT JOIN horas h ON e.id = h.empleado_id;
        """)

    col_emp = ["id", "nombre", "rol", "rendimiento", "estado"]
    col_jor = ["empleado", "hora_inicio", "hora_fin", "entrada", "salida"]

    list_emp = [dict(zip(col_emp, fila)) for fila in res_emp.rows]
    list_jor = [dict(zip(col_jor, fila)) for fila in res_jornada.rows]

    return list_emp, list_jor
  except Exception as e:
    logging.error(f"Error al obtener rendimiento y jornada: {e}")
    return [], []
  finally:
    await client.close()


async def obtener_datos_perfil(usuario_id: int):
  """Recupera la información del perfil del usuario."""
  client = obtener_cliente_turso()
  try:
    res = await client.execute(
        "SELECT id, nombre, email, telefono FROM usuario WHERE id = ?;",
        [usuario_id],
    )
    if res.rows:
      col = ["id", "nombre", "email", "telefono"]
      return dict(zip(col, res.rows[0]))
    return None
  except Exception as e:
    logging.error(f"Error al consultar perfil: {e}")
    return None
  finally:
    await client.close()


# ============================================================
# 🎬 HIGHLIGHTS LOCALES Y MONITOREO DE VIDEO
# ============================================================


def obtener_metadatos_video(nombre_archivo: str) -> dict:
  """Parsea metadatos de archivos de video almacenados localmente."""
  try:
    ruta_completa = os.path.join(VIDEOS_DIR, nombre_archivo)
    timestamp_creacion = os.path.getmtime(ruta_completa)
    fecha_creacion = datetime.datetime.fromtimestamp(timestamp_creacion)
  except (FileNotFoundError, OSError):
    fecha_creacion = datetime.datetime.now()

  partes = nombre_archivo.replace(".mp4", "").split("_")
  empleado = partes[0] if len(partes) > 0 else "Desconocido"
  actividad = partes[1] if len(partes) > 1 else "Actividad Detectada"

  if len(partes) >= 4:
    try:
      fecha_creacion = datetime.datetime.strptime(
          f"{partes[2]}_{partes[3]}", "%Y%m%d_%H%M%S"
      )
    except ValueError:
      pass

  return {
      "archivo": nombre_archivo,
      "empleado": empleado,
      "actividad": actividad,
      "fecha": fecha_creacion.strftime("%Y-%m-%d"),
      "hora": fecha_creacion.strftime("%H:%M:%S"),
      "timestamp": fecha_creacion.timestamp(),
      "url_reproduccion": (
          f"http://localhost:8000/static/videos/{nombre_archivo}"
      ),
  }


def listar_highlights_totales() -> list:
  """Lista los videos de highlights disponibles en el servidor local."""
  if not os.path.exists(VIDEOS_DIR):
    return []
  lista = [
      obtener_metadatos_video(arch)
      for arch in os.listdir(VIDEOS_DIR)
      if arch.endswith((".mp4", ".avi", ".mkv"))
  ]
  lista.sort(key=lambda x: x["timestamp"], reverse=True)
  return lista

# ============================================================
# 🗑️ CAPA DE DATOS: BORRADO DE ALERTAS Y HIGHLIGHTS
# ============================================================


async def borrar_alerta(alerta_id: int) -> dict:
  """Elimina una alerta por su ID en Turso."""
  async with obtener_cliente_turso() as client:
    try:
      await client.execute("DELETE FROM alerta WHERE id = ?;", [alerta_id])
      logging.info(f"Alerta ID {alerta_id} eliminada con éxito.")
      return {"exito": True, "mensaje": f"Alerta ID {alerta_id} eliminada."}
    except Exception as e:
      logging.error(f"Fallo al borrar alerta ID {alerta_id}: {e}")
      return {"exito": False, "mensaje": str(e)}


async def borrar_highlight(highlight_id: int) -> dict:
  """Elimina un highlight / registro de video por su ID en Turso."""
  async with obtener_cliente_turso() as client:
    try:
      await client.execute("DELETE FROM highlights WHERE id = ?;", [highlight_id])
      logging.info(f"Highlight ID {highlight_id} eliminado con éxito.")
      return {
          "exito": True,
          "mensaje": f"Highlight ID {highlight_id} eliminado.",
      }
    except Exception as e:
      logging.error(f"Fallo al borrar highlight ID {highlight_id}: {e}")
      return {"exito": False, "mensaje": str(e)}


# Aliases de compatibilidad
eliminar_alerta = borrar_alerta
eliminar_movimiento = borrar_highlight