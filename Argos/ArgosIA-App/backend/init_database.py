"""Compatibilidad con el nombre del script original; solo verifica, nunca crea tablas."""

import asyncio
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.SPs import (
    DatabaseConfigurationError,
    DatabaseSchemaError,
    DatabaseUnavailableError,
    verificar_esquema_y_conexion,
)


async def inicializar_estructura_base_datos() -> bool:
    """Verifica el esquema sin ejecutar CREATE, ALTER, DROP ni INSERT."""
    await verificar_esquema_y_conexion()
    print("Conexión disponible y esquema compatible. No se modificó la base de datos.")
    return True


if __name__ == "__main__":
    try:
        asyncio.run(inicializar_estructura_base_datos())
    except DatabaseConfigurationError as exc:
        print(str(exc))
        raise SystemExit(2) from None
    except DatabaseUnavailableError:
        print("Turso no está disponible. Revisá la red y la configuración local.")
        raise SystemExit(3) from None
    except DatabaseSchemaError as exc:
        print(str(exc))
        raise SystemExit(4) from None
    except Exception:
        print("No se pudo verificar la base. No se ejecutaron cambios.")
        raise SystemExit(5) from None
