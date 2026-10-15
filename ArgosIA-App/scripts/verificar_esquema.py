"""Muestra el esquema remoto de forma de solo lectura; nunca imprime credenciales."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.db_config import DatabaseConfigurationError, DatabaseUnavailableError, obtener_cliente_turso


async def main() -> int:
    client = None
    stage = "iniciar la conexión"
    try:
        client = obtener_cliente_turso()
        stage = "leer las tablas"
        tables = await client.execute(
            "SELECT name, sql FROM sqlite_schema WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name;"
        )
        if not tables.rows:
            print("Turso respondió, pero no hay tablas de aplicación visibles.")
            return 1
        print("Esquema activo de Turso (lectura solamente):")
        for table_name, create_sql in tables.rows:
            name = str(table_name)
            quoted_name = name.replace('"', '""')
            stage = "leer las columnas"
            columns = await client.execute(f'PRAGMA table_info("{quoted_name}");')
            definitions = []
            for row in (columns.rows or []):
                column_name, column_type, is_pk = str(row[1]), str(row[2] or ""), int(row[5] or 0)
                details = f"{column_name} {column_type}".strip()
                if is_pk:
                    details += " PRIMARY KEY"
                definitions.append(details)
            autoincrement = " AUTOINCREMENT" in str(create_sql or "").upper()
            print(f"- {name}: {', '.join(definitions)}; AUTOINCREMENT={'sí' if autoincrement else 'no'}")
        return 0
    except DatabaseConfigurationError as exc:
        print(str(exc))
        return 2
    except DatabaseUnavailableError:
        print("Turso no está disponible. Revisá la red y la configuración local.")
        return 3
    except Exception as exc:
        # Informar tipo y etapa ayuda a diagnosticar; nunca se imprime el mensaje
        # crudo del driver, que podría incluir la URL u otros datos de conexión.
        print(f"No se pudo {stage} ({type(exc).__name__}). No se ejecutaron cambios.")
        return 4
    finally:
        if client is not None:
            try:
                await client.close()
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
