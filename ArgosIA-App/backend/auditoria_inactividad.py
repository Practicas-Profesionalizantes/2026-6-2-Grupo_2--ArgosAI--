"""Auditoría opcional de inactividad; las alertas se limitan a una por ventana."""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.SPs import guardar_alerta
from backend.db_config import obtener_cliente_turso

logger = logging.getLogger(__name__)
MINUTOS_TOLERANCIA_INACTIVIDAD = 15


def mapear_dia_semana_espanol(numero_dia_python: int) -> str | None:
    days = {0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves", 4: "Viernes", 5: "Sábado", 6: "Domingo"}
    return days.get(numero_dia_python)


async def verificar_inactividad_tiempo_real() -> None:
    now = datetime.now().astimezone()
    now_text = now.strftime("%Y-%m-%d %H:%M:%S")
    current_time = now.strftime("%H:%M:%S")
    day_name = mapear_dia_semana_espanol(now.weekday())
    client = None
    try:
        client = obtener_cliente_turso()
        query = """
            SELECT DISTINCT e.id, e.nombre
            FROM empleado AS e
            INNER JOIN turno AS t ON t.empleado_id = e.id
            INNER JOIN diasTurno AS dt ON dt.turno_id = t.id
            INNER JOIN diasSemana AS ds ON ds.id = dt.diaSemana_id
            WHERE lower(e.estado) = 'activo' AND ds.dia = ?
              AND (
                (t.HoraInicio <= t.HoraFin AND ? BETWEEN t.HoraInicio AND t.HoraFin)
                OR
                (t.HoraInicio > t.HoraFin AND (? >= t.HoraInicio OR ? <= t.HoraFin))
              );
        """
        employees = await client.execute(query, [day_name, current_time, current_time, current_time])
        for row in (employees.rows or []):
            employee_id, employee_name = int(row[0]), str(row[1] or "Empleado")
            activity = await client.execute(
                """SELECT 1 FROM actividad
                   WHERE empleado_id = ?
                     AND datetime(fechaYHoraComienzo) BETWEEN datetime(?, ?) AND datetime(?)
                   LIMIT 1;""",
                [
                    employee_id,
                    now_text,
                    f"-{MINUTOS_TOLERANCIA_INACTIVIDAD} minutes",
                    now_text,
                ],
            )
            if activity.rows:
                continue

            description = f"Inactividad superior a {MINUTOS_TOLERANCIA_INACTIVIDAD} minutos."
            duplicate = await client.execute(
                """SELECT 1 FROM alerta
                   WHERE empleado_id = ? AND incumplimiento = ?
                     AND datetime(fechaYHora) >= datetime(?, ?)
                   LIMIT 1;""",
                [employee_id, description, now_text, f"-{MINUTOS_TOLERANCIA_INACTIVIDAD} minutes"],
            )
            if duplicate.rows:
                continue

            await guardar_alerta("Alta", description, employee_id)
            logger.info("Se registró una alerta de inactividad para empleado ID %s.", employee_id)
    except Exception as exc:
        logger.warning("No se pudo completar la ronda de auditoría (%s).", type(exc).__name__)
    finally:
        if client is not None:
            try:
                await client.close()
            except Exception as exc:
                logger.warning("No se pudo cerrar una conexión de auditoría (%s).", type(exc).__name__)


async def main_loop() -> None:
    while True:
        await verificar_inactividad_tiempo_real()
        await asyncio.sleep(60)


if __name__ == "__main__":
    if os.getenv("ARGOS_ENABLE_AUDIT_WORKER", "false").strip().casefold() not in {"1", "true", "yes", "si"}:
        print("Auditoría automática desactivada. Configurá ARGOS_ENABLE_AUDIT_WORKER=true para habilitarla.")
    else:
        try:
            asyncio.run(main_loop())
        except KeyboardInterrupt:
            logger.info("Motor de auditoría de inactividad apagado.")
