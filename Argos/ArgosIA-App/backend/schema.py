"""Comprobación de solo lectura contra BaseDeDatosHeladeria.sql."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SchemaIssue:
    table: str
    detail: str

    def __str__(self) -> str:
        return f"{self.table}: {self.detail}"


class DatabaseSchemaError(RuntimeError):
    def __init__(self, issues: list[SchemaIssue]):
        self.issues = issues
        tables = ", ".join(issue.table for issue in issues)
        super().__init__(
            "El esquema de Turso no coincide con BaseDeDatosHeladeria.sql. "
            f"Revisá estas tablas: {tables}. No se modificó la base de datos."
        )


# Solo se validan las tablas y columnas usadas por las pantallas de la app.
EXPECTED_COLUMNS: dict[str, tuple[str, ...]] = {
    "usuario": ("id", "nombre", "email", "contrasenia", "telefono"),
    "rol_empleado": ("id", "nombreRol", "descripcion"),
    "empleado": ("id", "nombre", "genero", "rendimiento", "estado", "urlImagen", "rol_id"),
    "diasSemana": ("id", "dia"),
    "turno": ("id", "HoraInicio", "HoraFin", "empleado_id"),
    "diasTurno": ("id", "turno_id", "diaSemana_id"),
    "horas": ("id", "fechaYHoraEntrada", "fechaYHoraSalida", "empleado_id"),
    "horas_extra": ("id", "cantidad", "horas_id"),
    "actividad": ("id", "tipoActividad", "fechaYHoraComienzo", "fechaYHoraFin", "empleado_id"),
    "camara": ("id", "ubicacion", "estado"),
    "video": ("id", "ruta", "fecha", "duracion", "tamanoArchivo", "tiempoLimite", "camara_id"),
    "highlights": ("id", "minutoInicio", "minutoFin", "video_id", "actividad_id"),
    "mov_sospechoso": ("id", "minutoInicio", "minutoFin", "descripcionPersonaInvolucrada", "boundingBox", "video_id"),
    "alerta": ("id", "grado", "incumplimiento", "fechaYHora", "empleado_id"),
    "revision_alerta": (
        "id", "estadoRevision", "comentarios", "fechaYHoraRevision", "usuario_id", "alerta_id"
    ),
    "auditoria": ("id", "accion", "usuario_id", "tablaM", "registro_afectado_id", "fecha"),
}

GENERATED_ID_TABLES = {
    "rol_empleado", "empleado", "diasSemana", "turno", "diasTurno", "horas", "horas_extra",
    "actividad", "alerta", "revision_alerta", "auditoria",
}


async def comprobar_esquema(client) -> list[SchemaIssue]:
    issues: list[SchemaIssue] = []
    for table, expected in EXPECTED_COLUMNS.items():
        # El nombre procede de EXPECTED_COLUMNS, no de datos del usuario.
        result = await client.execute(f'PRAGMA table_info("{table}")')
        rows = result.rows or []
        actual = {str(row[1]).casefold(): (str(row[2] or "").upper(), int(row[5] or 0)) for row in rows}
        if not actual:
            issues.append(SchemaIssue(table, "no existe o no se puede consultar"))
            continue

        missing = [column for column in expected if column.casefold() not in actual]
        if missing:
            issues.append(SchemaIssue(table, "faltan columnas: " + ", ".join(missing)))

        if "id" in expected and table in GENERATED_ID_TABLES and "id" in actual:
            id_type, is_primary_key = actual["id"]
            if id_type != "INTEGER" or is_primary_key != 1:
                issues.append(
                    SchemaIssue(table, "id debe ser INTEGER PRIMARY KEY para generarse sin asignar un ID desde la app")
                )

    return issues
