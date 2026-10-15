"""Acceso parametrizado a datos para la interfaz ArgosIA.

SQLite/libSQL no ofrece procedimientos almacenados. Estas funciones son la capa
de datos de la app y usan las tablas ya definidas, sin crear ni alterar esquema.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import re
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta, timezone

from backend.db_config import (
    DatabaseConfigurationError,
    DatabaseUnavailableError,
    obtener_cliente_turso,
)
from backend.schema import DatabaseSchemaError, comprobar_esquema
from backend.storage import detect_video_duration, format_video_duration, media_url, safe_video_path

logger = logging.getLogger(__name__)


class ValidationError(ValueError):
    """Dato de formulario inválido o relación que cambió antes de guardar."""


class DatabaseOperationError(RuntimeError):
    """La conexión existe, pero la consulta no pudo completarse."""


def _log_database_exception(exc: Exception) -> None:
    # Se registra el tipo, no el texto del driver, para evitar exponer datos de conexión.
    logger.warning("Falló una operación de base de datos (%s).", type(exc).__name__)


@asynccontextmanager
async def _database_client():
    client = None
    try:
        client = obtener_cliente_turso()
        yield client
    except (ValidationError, DatabaseConfigurationError, DatabaseUnavailableError, DatabaseSchemaError, DatabaseOperationError):
        raise
    except Exception as exc:
        _log_database_exception(exc)
        raise DatabaseOperationError(
            "No se pudo completar la operación en Turso. Revisá la conexión, el esquema y los datos relacionados."
        ) from None
    finally:
        if client is not None:
            try:
                await client.close()
            except Exception as exc:
                _log_database_exception(exc)


def _rows_as_dicts(result, columns: tuple[str, ...]) -> list[dict]:
    return [dict(zip(columns, row)) for row in (result.rows or [])]


def _valid_id(value, field: str = "ID") -> int:
    try:
        number = int(value)
    except (TypeError, ValueError, OverflowError):
        raise ValidationError(f"{field} no es válido.") from None
    if number <= 0:
        raise ValidationError(f"{field} debe ser mayor que cero.")
    return number


def _valid_text(value, field: str, max_length: int = 180) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValidationError(f"Completá {field}.")
    if len(text) > max_length:
        raise ValidationError(f"{field} supera el máximo de {max_length} caracteres.")
    return text


def _valid_time(value, field: str) -> str:
    text = str(value or "").strip()
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(text, fmt).strftime("%H:%M:%S")
        except ValueError:
            continue
    raise ValidationError(f"{field} no tiene un horario válido.")


def _minutes(value: str) -> int:
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            parsed = datetime.strptime(value, fmt)
            return parsed.hour * 60 + parsed.minute
        except ValueError:
            continue
    raise ValueError("Horario inválido")


def _duration_to_seconds(value: str) -> int:
    text = str(value or "").strip()
    if not re.fullmatch(r"\d{1,4}:[0-5]\d:[0-5]\d", text):
        raise ValidationError("El video no tiene una duración válida registrada.")
    hours, minutes, seconds = (int(part) for part in text.split(":"))
    return hours * 3600 + minutes * 60 + seconds


def _time_to_seconds(value: str) -> int:
    text = _valid_time(value, "El tramo")
    hours, minutes, seconds = (int(part) for part in text.split(":"))
    return hours * 3600 + minutes * 60 + seconds


def _time_ranges_overlap(start_a: int, end_a: int, start_b: int, end_b: int) -> bool:
    ranges_a = [(start_a, end_a)] if end_a > start_a else [(start_a, 1440), (0, end_a)]
    ranges_b = [(start_b, end_b)] if end_b > start_b else [(start_b, 1440), (0, end_b)]
    return any(max(left_a, left_b) < min(right_a, right_b) for left_a, right_a in ranges_a for left_b, right_b in ranges_b)


def verify_password(plain_password: str, stored_hash: str | None) -> bool:
    """Verifica el SHA-256 que ya usa la base y un formato PBKDF2 para una migración futura."""
    if not isinstance(plain_password, str) or not plain_password or len(plain_password) > 1024:
        return False
    if not stored_hash:
        return False
    stored = str(stored_hash).strip()

    if stored.startswith("pbkdf2_sha256$"):
        try:
            _, rounds_raw, salt_hex, digest_hex = stored.split("$", 3)
            rounds = int(rounds_raw)
            if rounds < 100_000 or rounds > 2_000_000 or not re.fullmatch(r"[0-9a-fA-F]{32,128}", salt_hex):
                return False
            expected = bytes.fromhex(digest_hex)
            actual = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), bytes.fromhex(salt_hex), rounds)
            return hmac.compare_digest(actual, expected)
        except (ValueError, TypeError):
            return False

    # Compatibilidad requerida con las claves SHA-256 que ya están guardadas.
    legacy = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
    return hmac.compare_digest(legacy, stored.lower())


async def verificar_esquema_y_conexion() -> bool:
    async with _database_client() as client:
        await client.execute("SELECT 1;")
        issues = await comprobar_esquema(client)
        if issues:
            raise DatabaseSchemaError(issues)
        return True


async def verificar_conexion() -> bool:
    async with _database_client() as client:
        await client.execute("SELECT 1;")
        return True


async def autenticar_usuario(email: str, password: str) -> dict | None:
    email = str(email or "").strip()
    if not email or len(email) > 254 or "@" not in email:
        return None
    if not isinstance(password, str) or not password:
        return None

    async with _database_client() as client:
        result = await client.execute(
            "SELECT id, nombre, contrasenia FROM usuario WHERE lower(email) = lower(?);",
            [email],
        )
        if not result.rows:
            return None
        user_id, name, stored_hash = result.rows[0]
        if not verify_password(password, stored_hash):
            return None
        return {"id": int(user_id), "nombre": str(name or "Operador")}


async def obtener_roles() -> list[dict]:
    async with _database_client() as client:
        result = await client.execute(
            "SELECT id, nombreRol, descripcion FROM rol_empleado ORDER BY nombreRol COLLATE NOCASE, id;"
        )
        return _rows_as_dicts(result, ("id", "nombre", "descripcion"))


async def crear_rol(nombre: str, descripcion: str) -> int:
    nombre = _valid_text(nombre, "el nombre del puesto", 100)
    descripcion = str(descripcion or "").strip()
    if len(descripcion) > 500:
        raise ValidationError("La descripción del puesto supera 500 caracteres.")
    async with _database_client() as client:
        duplicate = await client.execute(
            "SELECT 1 FROM rol_empleado WHERE lower(nombreRol) = lower(?) LIMIT 1;",
            [nombre],
        )
        if duplicate.rows:
            raise ValidationError("Ya existe un puesto con ese nombre.")
        result = await client.execute(
            "INSERT INTO rol_empleado (nombreRol, descripcion) VALUES (?, ?) RETURNING id;",
            [nombre, descripcion],
        )
        if not result.rows:
            raise DatabaseOperationError("No se pudo confirmar el ID del puesto guardado.")
        return int(result.rows[0][0])


async def eliminar_rol(rol_id) -> bool:
    """Elimina solo un puesto sin empleados asociados, conservando integridad."""
    rol_id = _valid_id(rol_id, "Puesto")
    async with _database_client() as client:
        result = await client.execute(
            "DELETE FROM rol_empleado WHERE id = ? AND NOT EXISTS "
            "(SELECT 1 FROM empleado WHERE rol_id = ?) RETURNING id;",
            [rol_id, rol_id],
        )
        if not result.rows:
            exists = await client.execute("SELECT 1 FROM rol_empleado WHERE id = ?;", [rol_id])
            if not exists.rows:
                raise ValidationError("El puesto ya no existe. Actualizá la lista.")
            raise ValidationError("No se puede borrar este puesto porque hay empleados asociados.")
        return True


async def obtener_auditoria(limite: int = 500) -> list[dict]:
    try:
        limite = min(2000, max(1, int(limite)))
    except (TypeError, ValueError, OverflowError):
        limite = 500
    async with _database_client() as client:
        result = await client.execute(
            """SELECT a.id, a.accion, a.usuario_id, u.nombre, a.tablaM,
                      a.registro_afectado_id,
                      CASE WHEN a.usuario_id IS NULL OR a.fecha LIKE '%+00:00'
                           THEN datetime(a.fecha, '-3 hours') ELSE a.fecha END
               FROM auditoria AS a LEFT JOIN usuario AS u ON u.id = a.usuario_id
               ORDER BY a.fecha DESC, a.id DESC LIMIT ?;""",
            [limite],
        )
        return _rows_as_dicts(
            result, ("id", "accion", "usuario_id", "usuario", "tabla", "registro_id", "fecha")
        )


async def registrar_auditoria_accion(usuario_id, accion: str, tabla: str, registro_id=None) -> bool:
    """Guarda quién ejecutó una acción manual, sin cambiar las columnas existentes."""
    usuario_id = _valid_id(usuario_id, "Usuario")
    allowed_tables = {
        "rol_empleado", "empleado", "diasSemana", "turno", "horas", "video",
        "highlights", "mov_sospechoso", "alerta", "revision_alerta",
    }
    if tabla not in allowed_tables:
        raise ValidationError("La tabla de auditoría no es válida.")
    action = _valid_text(accion, "la acción auditada", 300)
    if registro_id is not None:
        registro_id = _valid_id(registro_id, "Registro")
    async with _database_client() as client:
        user = await client.execute("SELECT nombre FROM usuario WHERE id = ?;", [usuario_id])
        if not user.rows:
            raise ValidationError("La sesión de usuario ya no es válida. Iniciá sesión de nuevo.")
        user_name = _valid_text(user.rows[0][0], "el nombre del usuario", 180)
        result = await client.execute(
            "INSERT INTO auditoria (accion, usuario_id, tablaM, registro_afectado_id, fecha) "
            "VALUES (?, ?, ?, ?, ?);",
            [f"{action} — Usuario: {user_name}", usuario_id, tabla, registro_id,
             datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S+00:00")],
        )
        return result is not None


async def obtener_empleados(incluir_inactivos: bool = True) -> list[dict]:
    query = """
        SELECT e.id, e.nombre, e.genero, e.rendimiento, e.estado, e.urlImagen,
               e.rol_id, r.nombreRol
        FROM empleado AS e
        LEFT JOIN rol_empleado AS r ON r.id = e.rol_id
    """
    params: list = []
    if not incluir_inactivos:
        query += " WHERE lower(COALESCE(e.estado, '')) = lower(?)"
        params.append("Activo")
    query += " ORDER BY e.nombre COLLATE NOCASE, e.id;"

    async with _database_client() as client:
        result = await client.execute(query, params)
        return _rows_as_dicts(
            result,
            ("id", "nombre", "genero", "rendimiento", "estado", "urlImagen", "rol_id", "puesto"),
        )


async def crear_empleado(nombre: str, genero: str, rendimiento: float, rol_id, estado: str = "Activo") -> int:
    nombre = _valid_text(nombre, "el nombre del empleado", 180)
    genero = _valid_text(genero, "el género", 40)
    estado = _valid_text(estado, "el estado", 30)
    if estado.casefold() not in {"activo", "inactivo"}:
        raise ValidationError("El estado debe ser Activo o Inactivo.")
    try:
        rendimiento = float(rendimiento)
    except (TypeError, ValueError, OverflowError):
        raise ValidationError("El rendimiento debe ser un número entre 0 y 100.") from None
    if not 0 <= rendimiento <= 100:
        raise ValidationError("El rendimiento debe estar entre 0 y 100.")
    rol_id = _valid_id(rol_id, "Puesto")

    async with _database_client() as client:
        role = await client.execute("SELECT 1 FROM rol_empleado WHERE id = ?;", [rol_id])
        if not role.rows:
            raise ValidationError("El puesto seleccionado ya no existe. Actualizá la lista e intentá de nuevo.")
        result = await client.execute(
            """INSERT INTO empleado
               (nombre, genero, rendimiento, estado, urlImagen, rol_id)
               VALUES (?, ?, ?, ?, NULL, ?) RETURNING id;""",
            [nombre, genero, rendimiento, estado.capitalize(), rol_id],
        )
        if not result.rows:
            raise DatabaseOperationError("No se pudo confirmar el ID del empleado guardado.")
        return int(result.rows[0][0])


async def actualizar_empleado(
    empleado_id, nombre: str, genero: str, rendimiento: float, estado: str, rol_id
) -> bool:
    empleado_id = _valid_id(empleado_id, "Empleado")
    nombre = _valid_text(nombre, "el nombre del empleado", 180)
    genero = _valid_text(genero, "el género", 40)
    estado = _valid_text(estado, "el estado", 30)
    if estado.casefold() not in {"activo", "inactivo"}:
        raise ValidationError("El estado debe ser Activo o Inactivo.")
    try:
        rendimiento = float(rendimiento)
    except (TypeError, ValueError, OverflowError):
        raise ValidationError("El rendimiento debe ser un número entre 0 y 100.") from None
    if not 0 <= rendimiento <= 100:
        raise ValidationError("El rendimiento debe estar entre 0 y 100.")
    rol_id = _valid_id(rol_id, "Puesto")

    async with _database_client() as client:
        employee = await client.execute("SELECT 1 FROM empleado WHERE id = ?;", [empleado_id])
        role = await client.execute("SELECT 1 FROM rol_empleado WHERE id = ?;", [rol_id])
        if not employee.rows:
            raise ValidationError("El empleado ya no existe. Actualizá la lista e intentá de nuevo.")
        if not role.rows:
            raise ValidationError("El puesto seleccionado ya no existe. Actualizá la lista e intentá de nuevo.")
        updated = await client.execute(
            "UPDATE empleado SET nombre = ?, genero = ?, rendimiento = ?, estado = ?, rol_id = ? WHERE id = ? RETURNING id;",
            [nombre, genero, rendimiento, estado, rol_id, empleado_id],
        )
        if not updated.rows:
            raise ValidationError("El empleado cambió antes de guardar. Actualizá la lista e intentá de nuevo.")
        return True


async def actualizar_ruta_imagen(empleado_id, ruta_relativa: str) -> bool:
    empleado_id = _valid_id(empleado_id, "Empleado")
    expected = f"biometria/empleado_{empleado_id}"
    if ruta_relativa != expected:
        raise ValidationError("La ruta de imagen no tiene el formato permitido.")
    async with _database_client() as client:
        updated = await client.execute(
            "UPDATE empleado SET urlImagen = ? WHERE id = ? RETURNING id;", [expected, empleado_id]
        )
        if not updated.rows:
            raise ValidationError("El empleado ya no existe. Actualizá la lista e intentá de nuevo.")
        return True


async def dar_de_baja_empleado(empleado_id, usuario_id, motivo: str) -> bool:
    empleado_id = _valid_id(empleado_id, "Empleado")
    usuario_id = _valid_id(usuario_id, "Usuario")
    motivo = _valid_text(motivo, "el motivo de la baja", 500)
    async with _database_client() as client:
        employee = await client.execute("SELECT 1 FROM empleado WHERE id = ?;", [empleado_id])
        user = await client.execute("SELECT nombre FROM usuario WHERE id = ?;", [usuario_id])
        if not employee.rows:
            raise ValidationError("El empleado ya no existe. Actualizá la lista e intentá de nuevo.")
        if not user.rows:
            raise ValidationError("La sesión de usuario ya no es válida. Iniciá sesión de nuevo.")
        # Conserva el historial, registra el motivo en la auditoría existente y actualiza atómicamente.
        # Una operación batch es atómica también sobre el transporte HTTP;
        # transaction() interactivo solo está disponible sobre WebSocket.
        result = await client.batch(
            [
                (
                    "UPDATE empleado SET estado = 'Inactivo' WHERE id = ? "
                    "AND EXISTS (SELECT 1 FROM usuario WHERE id = ?) RETURNING id;",
                    [empleado_id, usuario_id],
                ),
                (
                    """INSERT INTO auditoria (accion, usuario_id, tablaM, registro_afectado_id, fecha)
                       SELECT ?, ?, 'empleado', ?, ? WHERE changes() > 0;""",
                    [f"BAJA: {motivo} — Usuario: {str(user.rows[0][0] or 'Operador')[:180]}", usuario_id, empleado_id, datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S+00:00")],
                ),
            ]
        )
        if not result or not result[0].rows:
            raise ValidationError("El empleado o la sesión cambiaron antes de darlo de baja. Actualizá la lista.")
        return True


async def reintegrar_empleado(empleado_id) -> bool:
    empleado_id = _valid_id(empleado_id, "Empleado")
    async with _database_client() as client:
        result = await client.execute(
            "UPDATE empleado SET estado = 'Activo' WHERE id = ? AND lower(COALESCE(estado, '')) = 'inactivo' RETURNING id;",
            [empleado_id],
        )
        if not result.rows:
            employee = await client.execute("SELECT estado FROM empleado WHERE id = ?;", [empleado_id])
            if not employee.rows:
                raise ValidationError("El empleado ya no existe. Actualizá la lista.")
            raise ValidationError("El empleado ya no figura como dado de baja. Actualizá la lista.")
        return True


async def obtener_dias_semana() -> list[dict]:
    async with _database_client() as client:
        result = await client.execute("SELECT id, dia FROM diasSemana ORDER BY id;")
        return _rows_as_dicts(result, ("id", "dia"))


async def cargar_dias_semana_si_vacio() -> bool:
    """Inserta el catálogo estándar solo tras una acción explícita y si está vacío."""
    days = ("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo")
    async with _database_client() as client:
        values = " UNION ALL ".join("SELECT ? AS dia" if i == 0 else "SELECT ?" for i in range(len(days)))
        result = await client.execute(
            f"""INSERT INTO diasSemana (dia)
                SELECT dia FROM ({values}) WHERE NOT EXISTS (SELECT 1 FROM diasSemana)
                RETURNING id;""",
            list(days),
        )
        return bool(result.rows)


async def obtener_turnos() -> list[dict]:
    """Lista los turnos semanales definidos en turno y diasTurno."""
    query = """
        SELECT t.id, t.empleado_id, e.nombre, COALESCE(GROUP_CONCAT(DISTINCT ds.dia), ''), t.HoraInicio, t.HoraFin
        FROM turno AS t
        LEFT JOIN empleado AS e ON e.id = t.empleado_id
        LEFT JOIN diasTurno AS dt ON dt.turno_id = t.id
        LEFT JOIN diasSemana AS ds ON ds.id = dt.diaSemana_id
        GROUP BY t.id, t.empleado_id, e.nombre, t.HoraInicio, t.HoraFin
        ORDER BY e.nombre COLLATE NOCASE, t.HoraInicio, t.id;
    """
    async with _database_client() as client:
        result = await client.execute(query)
        return _rows_as_dicts(result, ("id", "empleado_id", "empleado", "dias", "hora_inicio", "hora_fin"))


async def asignar_turno_completo(empleado_id, hora_inicio: str, hora_fin: str, lista_dias_id) -> int:
    empleado_id = _valid_id(empleado_id, "Empleado")
    hora_inicio = _valid_time(hora_inicio, "La hora de entrada")
    hora_fin = _valid_time(hora_fin, "La hora de salida")
    if hora_inicio == hora_fin:
        raise ValidationError("La hora de salida debe ser distinta de la hora de entrada.")
    day_ids = sorted({_valid_id(value, "Día") for value in (lista_dias_id or [])})
    if not day_ids:
        raise ValidationError("Seleccioná al menos un día de la semana.")

    async with _database_client() as client:
        employee = await client.execute("SELECT 1 FROM empleado WHERE id = ?;", [empleado_id])
        if not employee.rows:
            raise ValidationError("El empleado seleccionado ya no existe.")
        for day_id in day_ids:
            day = await client.execute("SELECT 1 FROM diasSemana WHERE id = ?;", [day_id])
            if not day.rows:
                raise ValidationError("Uno de los días seleccionados ya no existe en la base de datos.")

        placeholders = ", ".join("?" for _ in day_ids)
        existing = await client.execute(
            f"""SELECT t.HoraInicio, t.HoraFin
                FROM turno AS t
                INNER JOIN diasTurno AS dt ON dt.turno_id = t.id
                WHERE t.empleado_id = ? AND dt.diaSemana_id IN ({placeholders});""",
            [empleado_id, *day_ids],
        )
        start_minutes, end_minutes = _minutes(hora_inicio), _minutes(hora_fin)
        for row in existing.rows or []:
            try:
                existing_start, existing_end = _minutes(str(row[0])), _minutes(str(row[1]))
            except (TypeError, ValueError):
                # Un registro histórico con formato inválido no debe bloquear otros horarios.
                continue
            if existing_start == existing_end:
                continue
            if _time_ranges_overlap(start_minutes, end_minutes, existing_start, existing_end):
                raise ValidationError("El empleado ya tiene un turno que se superpone en uno de esos días.")

        statements = [
            (
                "INSERT INTO turno (HoraInicio, HoraFin, empleado_id) VALUES (?, ?, ?) RETURNING id;",
                [hora_inicio, hora_fin, empleado_id],
            ),
            *[
                ("INSERT INTO diasTurno (turno_id, diaSemana_id) VALUES (last_insert_rowid(), ?);", [day_id])
                for day_id in day_ids
            ],
        ]
        results = await client.batch(statements)
        if not results or not results[0].rows:
            raise DatabaseOperationError("No se pudo confirmar el ID del turno guardado.")
        return int(results[0].rows[0][0])


async def actualizar_turno_completo(turno_id, empleado_id, hora_inicio: str, hora_fin: str, lista_dias_id) -> bool:
    turno_id = _valid_id(turno_id, "Turno")
    empleado_id = _valid_id(empleado_id, "Empleado")
    hora_inicio = _valid_time(hora_inicio, "La hora de entrada")
    hora_fin = _valid_time(hora_fin, "La hora de salida")
    if hora_inicio == hora_fin:
        raise ValidationError("La hora de salida debe ser distinta de la hora de entrada.")
    day_ids = sorted({_valid_id(value, "Día") for value in (lista_dias_id or [])})
    if not day_ids:
        raise ValidationError("Seleccioná al menos un día de la semana.")
    async with _database_client() as client:
        existing_shift = await client.execute("SELECT 1 FROM turno WHERE id = ?;", [turno_id])
        employee = await client.execute("SELECT 1 FROM empleado WHERE id = ?;", [empleado_id])
        if not existing_shift.rows:
            raise ValidationError("El turno ya no existe. Actualizá la lista.")
        if not employee.rows:
            raise ValidationError("El empleado seleccionado ya no existe.")
        placeholders = ", ".join("?" for _ in day_ids)
        overlaps = await client.execute(
            f"""SELECT t.HoraInicio, t.HoraFin FROM turno AS t
                INNER JOIN diasTurno AS dt ON dt.turno_id = t.id
                WHERE t.empleado_id = ? AND t.id <> ? AND dt.diaSemana_id IN ({placeholders});""",
            [empleado_id, turno_id, *day_ids],
        )
        start_minutes, end_minutes = _minutes(hora_inicio), _minutes(hora_fin)
        for row in overlaps.rows or []:
            try:
                existing_start, existing_end = _minutes(str(row[0])), _minutes(str(row[1]))
            except ValueError:
                continue
            if _time_ranges_overlap(start_minutes, end_minutes, existing_start, existing_end):
                raise ValidationError("El empleado ya tiene otro turno superpuesto en uno de esos días.")
        for day_id in day_ids:
            day = await client.execute("SELECT 1 FROM diasSemana WHERE id = ?;", [day_id])
            if not day.rows:
                raise ValidationError("Uno de los días seleccionados ya no existe.")
        statements = [
            ("UPDATE turno SET HoraInicio = ?, HoraFin = ?, empleado_id = ? WHERE id = ? RETURNING id;",
             [hora_inicio, hora_fin, empleado_id, turno_id]),
            ("DELETE FROM diasTurno WHERE turno_id = ?;", [turno_id]),
            *[("INSERT INTO diasTurno (turno_id, diaSemana_id) VALUES (?, ?);", [turno_id, day_id]) for day_id in day_ids],
        ]
        results = await client.batch(statements)
        if not results or not results[0].rows:
            raise ValidationError("El turno cambió antes de guardar. Actualizá la lista e intentá de nuevo.")
        return True


async def eliminar_turno(turno_id) -> bool:
    turno_id = _valid_id(turno_id, "Turno")
    async with _database_client() as client:
        exists = await client.execute("SELECT 1 FROM turno WHERE id = ?;", [turno_id])
        if not exists.rows:
            raise ValidationError("El turno ya no existe. Actualizá la lista.")
        results = await client.batch([
            ("DELETE FROM diasTurno WHERE turno_id = ?;", [turno_id]),
            ("DELETE FROM turno WHERE id = ? RETURNING id;", [turno_id]),
        ])
        if not results or not results[-1].rows:
            raise ValidationError("El turno cambió antes de borrar. Actualizá la lista e intentá de nuevo.")
        return True


async def obtener_jornadas_empleado(empleado_id, fecha: str) -> list[dict]:
    empleado_id = _valid_id(empleado_id, "Empleado")
    try:
        fecha = datetime.strptime(str(fecha), "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        raise ValidationError("La fecha no es válida.") from None
    query = """
        SELECT h.id, h.fechaYHoraEntrada, h.fechaYHoraSalida,
               COALESCE((SELECT SUM(he.cantidad) FROM horas_extra AS he WHERE he.horas_id = h.id), 0)
        FROM horas AS h
        WHERE h.empleado_id = ? AND substr(h.fechaYHoraEntrada, 1, 10) = ?
        ORDER BY h.fechaYHoraEntrada DESC, h.id DESC;
    """
    async with _database_client() as client:
        result = await client.execute(query, [empleado_id, fecha])
        return _rows_as_dicts(result, ("id", "entrada", "salida", "horas_extra"))


async def registrar_jornada_manual(empleado_id, fecha: str, entrada: str, salida: str) -> int:
    """Registra una fichada manual y calcula extra contra los turnos semanales."""
    empleado_id = _valid_id(empleado_id, "Empleado")
    try:
        selected_date = datetime.strptime(str(fecha), "%Y-%m-%d").date()
    except ValueError:
        raise ValidationError("La fecha de la jornada no es válida.") from None
    if selected_date > date.today():
        raise ValidationError("No se puede registrar como trabajada una fecha futura.")
    entrada = _valid_time(entrada, "La hora de entrada")
    salida = _valid_time(salida, "La hora de salida")
    start = datetime.combine(selected_date, datetime.strptime(entrada, "%H:%M:%S").time())
    end = datetime.combine(selected_date, datetime.strptime(salida, "%H:%M:%S").time())
    if end <= start:
        end += timedelta(days=1)
    worked = (end - start).total_seconds() / 3600
    if worked <= 0 or worked > 24:
        raise ValidationError("La jornada debe durar más de 0 y hasta 24 horas.")
    start_text = start.strftime("%Y-%m-%d %H:%M:%S")
    end_text = end.strftime("%Y-%m-%d %H:%M:%S")
    weekday = ("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo")[selected_date.weekday()]
    async with _database_client() as client:
        employee = await client.execute("SELECT 1 FROM empleado WHERE id = ?;", [empleado_id])
        if not employee.rows:
            raise ValidationError("El empleado ya no existe. Actualizá la lista.")
        existing_day = await client.execute(
            "SELECT 1 FROM horas WHERE empleado_id = ? AND substr(fechaYHoraEntrada, 1, 10) = ? LIMIT 1;",
            [empleado_id, selected_date.isoformat()],
        )
        if existing_day.rows:
            raise ValidationError("Ese empleado ya tiene una fichada ese día. Consultá la jornada para evitar duplicarla.")
        shifts = await client.execute(
            """SELECT t.HoraInicio, t.HoraFin FROM turno AS t
               INNER JOIN diasTurno AS dt ON dt.turno_id = t.id
               INNER JOIN diasSemana AS ds ON ds.id = dt.diaSemana_id
               WHERE t.empleado_id = ? AND lower(ds.dia) = lower(?);""",
            [empleado_id, weekday],
        )
        planned_hours = 0.0
        for row in shifts.rows or []:
            try:
                a = datetime.strptime(str(row[0]), "%H:%M:%S")
            except ValueError:
                a = datetime.strptime(str(row[0]), "%H:%M")
            try:
                b = datetime.strptime(str(row[1]), "%H:%M:%S")
            except ValueError:
                b = datetime.strptime(str(row[1]), "%H:%M")
            span = (b - a).total_seconds() / 3600
            planned_hours += span if span > 0 else span + 24
        overtime = worked if not shifts.rows else max(0.0, worked - planned_hours)
        shortfall = max(0.0, planned_hours - worked) if shifts.rows else 0.0
        batch = [
            ("INSERT INTO horas (fechaYHoraEntrada, fechaYHoraSalida, empleado_id) VALUES (?, ?, ?) RETURNING id;",
             [start_text, end_text, empleado_id]),
        ]
        if overtime > 0:
            batch.append(("INSERT INTO horas_extra (cantidad, horas_id) VALUES (?, last_insert_rowid());", [round(overtime, 2)]))
        results = await client.batch(batch)
        if not results or not results[0].rows:
            raise DatabaseOperationError("No se pudo confirmar la jornada registrada.")
        return int(results[0].rows[0][0])


async def obtener_resumen_dashboard() -> dict:
    async with _database_client() as client:
        active = await client.execute("SELECT COUNT(*) FROM empleado WHERE lower(estado) = 'activo';")
        alerts = await client.execute("SELECT COUNT(*) FROM alerta;")
        employees = await client.execute(
            """SELECT e.nombre, e.rendimiento, e.estado, r.nombreRol
               FROM empleado AS e LEFT JOIN rol_empleado AS r ON r.id = e.rol_id
               ORDER BY e.nombre COLLATE NOCASE, e.id;"""
        )
        return {
            "activos": int(active.rows[0][0]) if active.rows else 0,
            "alertas": int(alerts.rows[0][0]) if alerts.rows else 0,
            "filas": _rows_as_dicts(employees, ("nombre", "rendimiento", "estado", "puesto")),
        }


async def obtener_resumen_rendimiento(desde: str, hasta: str) -> dict:
    try:
        desde = datetime.strptime(str(desde), "%Y-%m-%d").strftime("%Y-%m-%d")
        hasta = datetime.strptime(str(hasta), "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        raise ValidationError("El período seleccionado no es válido.") from None
    if desde > hasta:
        raise ValidationError("La fecha inicial debe ser anterior a la fecha final.")

    async with _database_client() as client:
        active = await client.execute(
            "SELECT COUNT(*), COALESCE(AVG(CAST(rendimiento AS REAL)), 0) FROM empleado WHERE lower(estado) = 'activo';"
        )
        hours = await client.execute(
            """SELECT COALESCE(SUM((julianday(fechaYHoraSalida) - julianday(fechaYHoraEntrada)) * 24), 0)
               FROM horas
               WHERE fechaYHoraSalida IS NOT NULL
                 AND date(fechaYHoraEntrada) BETWEEN ? AND ?;""",
            [desde, hasta],
        )
        alerts = await client.execute(
            "SELECT COUNT(*) FROM alerta WHERE date(fechaYHora) BETWEEN ? AND ?;",
            [desde, hasta],
        )
        employees = await client.execute(
            """SELECT e.id, e.nombre, r.nombreRol, e.rendimiento, e.estado,
                 (SELECT COUNT(*) FROM actividad AS a
                  WHERE a.empleado_id = e.id AND a.fechaYHoraFin IS NOT NULL
                    AND date(a.fechaYHoraComienzo) BETWEEN ? AND ?) AS tareas,
                 (SELECT COALESCE(SUM((julianday(h.fechaYHoraSalida) - julianday(h.fechaYHoraEntrada)) * 24), 0)
                  FROM horas AS h
                  WHERE h.empleado_id = e.id AND h.fechaYHoraSalida IS NOT NULL
                    AND date(h.fechaYHoraEntrada) BETWEEN ? AND ?) AS horas,
                 (SELECT COUNT(*) FROM alerta AS al
                  WHERE al.empleado_id = e.id AND date(al.fechaYHora) BETWEEN ? AND ?) AS alertas
               FROM empleado AS e
               LEFT JOIN rol_empleado AS r ON r.id = e.rol_id
               ORDER BY e.nombre COLLATE NOCASE, e.id;""",
            [desde, hasta, desde, hasta, desde, hasta],
        )
        rows = _rows_as_dicts(
            employees,
            ("id", "nombre", "rol", "rendimiento", "estado", "tareas", "horas", "alertas"),
        )
        for row in rows:
            row["horas"] = max(0.0, float(row.get("horas") or 0.0))
        return {
            "activos": int(active.rows[0][0]) if active.rows else 0,
            "eficiencia": round(float(active.rows[0][1] or 0), 1) if active.rows else 0,
            "horas": max(0.0, float(hours.rows[0][0] or 0.0)) if hours.rows else 0.0,
            "alertas": int(alerts.rows[0][0]) if alerts.rows else 0,
            "filas": rows,
        }


async def obtener_camaras() -> list[dict]:
    async with _database_client() as client:
        result = await client.execute(
            "SELECT id, ubicacion, estado FROM camara ORDER BY ubicacion COLLATE NOCASE, id;"
        )
        return _rows_as_dicts(result, ("id", "ubicacion", "estado"))


async def obtener_eventos_seguridad(desde: str | None = None, hasta: str | None = None) -> list[dict]:
    """Consulta movimientos sospechosos y sus clips/cámaras relacionados."""
    query = """
        SELECT m.id, m.minutoInicio, m.minutoFin, m.descripcionPersonaInvolucrada,
               m.boundingBox, v.ruta, v.fecha, v.duracion, c.ubicacion, c.id
        FROM mov_sospechoso AS m
        LEFT JOIN video AS v ON v.id = m.video_id
        LEFT JOIN camara AS c ON c.id = v.camara_id
    """
    params: list = []
    if desde is not None or hasta is not None:
        try:
            desde = datetime.strptime(str(desde), "%Y-%m-%d").strftime("%Y-%m-%d")
            hasta = datetime.strptime(str(hasta), "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError:
            raise ValidationError("El período seleccionado no es válido.") from None
        if desde > hasta:
            raise ValidationError("La fecha inicial debe ser anterior a la fecha final.")
        query += " WHERE v.fecha IS NULL OR date(v.fecha) BETWEEN ? AND ?"
        params.extend([desde, hasta])
    query += " ORDER BY v.fecha DESC, m.id DESC;"
    async with _database_client() as client:
        result = await client.execute(query, params)
        rows = _rows_as_dicts(
            result,
            ("id", "inicio", "fin", "descripcion", "bounding_box", "ruta", "fecha", "duracion", "camara", "camara_id"),
        )
        for row in rows:
            path = safe_video_path(row.get("ruta"))
            row["archivo"] = path.name if path else None
            row["url_reproduccion"] = media_url(path.name) if path else None
        return rows


async def registrar_video(ruta: str, fecha: str, tamano_bytes: int, camara_id) -> int:
    """Registra metadatos de un clip local en video; el binario permanece local."""
    filename = str(ruta or "").replace("\\", "/").split("/")[-1]
    if not filename or filename != str(ruta).replace("\\", "/"):
        raise ValidationError("La ruta del video no es válida.")
    local_video = safe_video_path(filename)
    if local_video is None:
        raise ValidationError("El archivo de video no existe en la carpeta multimedia local.")
    try:
        timestamp = datetime.strptime(str(fecha), "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise ValidationError("La fecha del video no es válida.") from None
    try:
        byte_count = int(tamano_bytes)
    except (TypeError, ValueError, OverflowError):
        raise ValidationError("El tamaño del video no es válido.") from None
    if byte_count <= 0 or byte_count > 200 * 1024 * 1024:
        raise ValidationError("El video debe pesar hasta 200 MB.")
    duracion = format_video_duration(detect_video_duration(local_video))
    camara_id = _valid_id(camara_id, "Cámara") if camara_id not in (None, "") else None
    async with _database_client() as client:
        if camara_id is not None:
            camera = await client.execute("SELECT 1 FROM camara WHERE id = ?;", [camara_id])
            if not camera.rows:
                raise ValidationError("La cámara seleccionada ya no existe.")
        result = await client.execute(
            "INSERT INTO video (ruta, fecha, duracion, tamanoArchivo, tiempoLimite, camara_id) "
            "VALUES (?, ?, ?, ?, NULL, ?) RETURNING id;",
            [filename, timestamp, duracion, byte_count / (1024 * 1024), camara_id],
        )
        if not result.rows:
            raise DatabaseOperationError("No se pudo confirmar el video cargado.")
        return int(result.rows[0][0])


async def obtener_actividades(fecha: str | None = None) -> list[dict]:
    query = """SELECT a.id, a.tipoActividad, a.fechaYHoraComienzo, a.fechaYHoraFin,
                      a.empleado_id, e.nombre
               FROM actividad AS a LEFT JOIN empleado AS e ON e.id = a.empleado_id"""
    params: list = []
    if fecha:
        try:
            fecha = datetime.strptime(str(fecha), "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError:
            raise ValidationError("La fecha seleccionada no es válida.") from None
        query += " WHERE date(a.fechaYHoraComienzo) = ?"
        params.append(fecha)
    query += " ORDER BY a.fechaYHoraComienzo DESC, a.id DESC LIMIT 1000;"
    async with _database_client() as client:
        result = await client.execute(query, params)
        return _rows_as_dicts(result, ("id", "tipo", "inicio", "fin", "empleado_id", "empleado"))


async def registrar_highlight(video_id, actividad_id, minuto_inicio: str, minuto_fin: str) -> int:
    video_id = _valid_id(video_id, "Video")
    actividad_id = _valid_id(actividad_id, "Actividad")
    minute_start = _valid_time(minuto_inicio, "El inicio del highlight")
    minute_end = _valid_time(minuto_fin, "El fin del highlight")
    if _time_to_seconds(minute_end) <= _time_to_seconds(minute_start):
        raise ValidationError("El fin del highlight debe ser posterior al inicio.")
    async with _database_client() as client:
        video = await client.execute("SELECT duracion FROM video WHERE id = ?;", [video_id])
        if not video.rows:
            raise ValidationError("El video seleccionado ya no existe.")
        duration = _duration_to_seconds(video.rows[0][0])
        if _time_to_seconds(minute_end) > duration:
            raise ValidationError("El tramo debe estar dentro de la duración del video.")
        result = await client.execute(
            "INSERT INTO highlights (minutoInicio, minutoFin, video_id, actividad_id) "
            "SELECT ?, ?, ?, ? WHERE EXISTS (SELECT 1 FROM video WHERE id = ?) "
            "AND EXISTS (SELECT 1 FROM actividad WHERE id = ?) RETURNING id;",
            [minute_start, minute_end, video_id, actividad_id, video_id, actividad_id],
        )
        if not result.rows:
            raise ValidationError("El video o la actividad seleccionados ya no existen.")
        return int(result.rows[0][0])


async def registrar_evento_seguridad(video_id, minuto_inicio: str, minuto_fin: str, descripcion: str) -> int:
    video_id = _valid_id(video_id, "Video")
    start = _valid_time(minuto_inicio, "El inicio del evento")
    end = _valid_time(minuto_fin, "El fin del evento")
    if _time_to_seconds(end) <= _time_to_seconds(start):
        raise ValidationError("El fin del evento debe ser posterior al inicio.")
    descripcion = _valid_text(descripcion, "la descripción del evento", 500)
    async with _database_client() as client:
        video = await client.execute("SELECT duracion FROM video WHERE id = ?;", [video_id])
        if not video.rows:
            raise ValidationError("El video seleccionado ya no existe.")
        duration = _duration_to_seconds(video.rows[0][0])
        if _time_to_seconds(end) > duration:
            raise ValidationError("El tramo debe estar dentro de la duración del video.")
        result = await client.execute(
            "INSERT INTO mov_sospechoso (minutoInicio, minutoFin, descripcionPersonaInvolucrada, boundingBox, video_id) "
            "SELECT ?, ?, ?, NULL, ? WHERE EXISTS (SELECT 1 FROM video WHERE id = ?) RETURNING id;",
            [start, end, descripcion, video_id, video_id],
        )
        if not result.rows:
            raise ValidationError("El video seleccionado ya no existe.")
        return int(result.rows[0][0])


async def buscar_grabaciones(fecha: str, camara_id, franja: str) -> list[dict]:
    try:
        fecha = datetime.strptime(str(fecha), "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        raise ValidationError("La fecha seleccionada no es válida.") from None
    camara_id = _valid_id(camara_id, "Cámara")
    slots = {"00:00–06:00": (0, 6), "06:00–12:00": (6, 12), "12:00–18:00": (12, 18), "18:00–24:00": (18, 24)}
    if franja not in slots:
        raise ValidationError("La franja horaria seleccionada no es válida.")
    query = """
        SELECT id, ruta, fecha, duracion, tamanoArchivo, tiempoLimite
        FROM video
        WHERE camara_id = ? AND date(fecha) = ?
        ORDER BY fecha DESC, id DESC;
    """
    async with _database_client() as client:
        result = await client.execute(query, [camara_id, fecha])
        found = []
        start_hour, end_hour = slots[franja]
        for row in (result.rows or []):
            try:
                raw_date = str(row[2] or "")
                date_time = datetime.fromisoformat(raw_date.replace("Z", "+00:00")) if len(raw_date.strip()) > 10 else None
            except (TypeError, ValueError):
                date_time = None
            if date_time is not None and (date_time.hour < start_hour or date_time.hour >= end_hour):
                continue
            path = safe_video_path(row[1])
            found.append(
                {
                    "id": int(row[0]),
                    "archivo": path.name if path else None,
                    "fecha": row[2],
                    "duracion": row[3],
                    "tamano": row[4],
                    "tiempo_limite": row[5],
                    "url_reproduccion": media_url(path.name) if path else None,
                    "franja_aplicable": date_time is not None,
                }
            )
        return found


async def buscar_videos_recientes(limite: int = 500) -> list[dict]:
    try:
        limite = min(2000, max(1, int(limite)))
    except (TypeError, ValueError, OverflowError):
        limite = 500
    async with _database_client() as client:
        result = await client.execute(
            "SELECT id, ruta, fecha, duracion, camara_id FROM video ORDER BY fecha DESC, id DESC LIMIT ?;",
            [limite],
        )
        rows = _rows_as_dicts(result, ("id", "ruta", "fecha", "duracion", "camara_id"))
        for row in rows:
            path = safe_video_path(row.get("ruta"))
            row["archivo"] = path.name if path else None
            row["url_reproduccion"] = media_url(path.name) if path else None
        return rows


async def obtener_alertas() -> list[dict]:
    query = """
        SELECT a.id, a.grado, a.incumplimiento, a.fechaYHora, a.empleado_id, e.nombre
        FROM alerta AS a
        LEFT JOIN empleado AS e ON e.id = a.empleado_id
        ORDER BY a.fechaYHora DESC, a.id DESC;
    """
    async with _database_client() as client:
        result = await client.execute(query)
        return _rows_as_dicts(result, ("id", "grado", "incumplimiento", "fecha", "empleado_id", "empleado"))


async def guardar_alerta(grado: str, incumplimiento: str, empleado_id) -> int:
    grado = _valid_text(grado, "la gravedad", 30)
    if grado.casefold() not in {"alta", "media", "baja"}:
        raise ValidationError("La gravedad debe ser Alta, Media o Baja.")
    incumplimiento = _valid_text(incumplimiento, "la descripción", 1000)
    empleado_id = _valid_id(empleado_id, "Empleado")
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    async with _database_client() as client:
        employee = await client.execute("SELECT 1 FROM empleado WHERE id = ?;", [empleado_id])
        if not employee.rows:
            raise ValidationError("El empleado seleccionado ya no existe.")
        result = await client.execute(
            "INSERT INTO alerta (grado, incumplimiento, fechaYHora, empleado_id) VALUES (?, ?, ?, ?) RETURNING id;",
            [grado, incumplimiento, fecha, empleado_id],
        )
        if not result.rows:
            raise DatabaseOperationError("No se pudo confirmar la alerta guardada.")
        return int(result.rows[0][0])


async def registrar_revision_alerta(alerta_id, usuario_id, estado: str, comentarios: str) -> int:
    alerta_id = _valid_id(alerta_id, "Alerta")
    usuario_id = _valid_id(usuario_id, "Usuario")
    estado = _valid_text(estado, "el estado de revisión", 40)
    comentarios = str(comentarios or "").strip()
    if len(comentarios) > 1000:
        raise ValidationError("El comentario supera 1000 caracteres.")
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    async with _database_client() as client:
        alert = await client.execute("SELECT 1 FROM alerta WHERE id = ?;", [alerta_id])
        user = await client.execute("SELECT 1 FROM usuario WHERE id = ?;", [usuario_id])
        if not alert.rows:
            raise ValidationError("La alerta ya no existe.")
        if not user.rows:
            raise ValidationError("La sesión de usuario ya no es válida. Iniciá sesión de nuevo.")
        result = await client.execute(
            """INSERT INTO revision_alerta
               (estadoRevision, comentarios, fechaYHoraRevision, usuario_id, alerta_id)
               VALUES (?, ?, ?, ?, ?) RETURNING id;""",
            [estado, comentarios, fecha, usuario_id, alerta_id],
        )
        if not result.rows:
            raise DatabaseOperationError("No se pudo confirmar la revisión guardada.")
        return int(result.rows[0][0])


async def obtener_highlights(fecha: str | None = None) -> list[dict]:
    query = """
        SELECT h.id, h.minutoInicio, h.minutoFin, v.ruta, v.fecha, v.duracion,
               a.tipoActividad, a.empleado_id, e.nombre
        FROM highlights AS h
        INNER JOIN video AS v ON v.id = h.video_id
        INNER JOIN actividad AS a ON a.id = h.actividad_id
        LEFT JOIN empleado AS e ON e.id = a.empleado_id
    """
    params: list = []
    if fecha is not None:
        try:
            fecha = datetime.strptime(str(fecha), "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError:
            raise ValidationError("La fecha seleccionada no es válida.") from None
        query += " WHERE date(v.fecha) = ?"
        params.append(fecha)
    query += " ORDER BY v.fecha DESC, h.id DESC;"
    async with _database_client() as client:
        result = await client.execute(query, params)
        rows = _rows_as_dicts(
            result,
            ("id", "minuto_inicio", "minuto_fin", "ruta", "fecha", "duracion", "actividad", "empleado_id", "empleado"),
        )
        for row in rows:
            path = safe_video_path(row.get("ruta"))
            row["archivo"] = path.name if path else None
            row["url_reproduccion"] = media_url(path.name) if path else None
        return rows


async def obtener_revisiones_alerta(alerta_id) -> list[dict]:
    alerta_id = _valid_id(alerta_id, "Alerta")
    async with _database_client() as client:
        result = await client.execute(
            """SELECT id, estadoRevision, comentarios, fechaYHoraRevision
               FROM revision_alerta WHERE alerta_id = ?
               ORDER BY fechaYHoraRevision DESC, id DESC;""",
            [alerta_id],
        )
        return _rows_as_dicts(result, ("id", "estado", "comentarios", "fecha"))

