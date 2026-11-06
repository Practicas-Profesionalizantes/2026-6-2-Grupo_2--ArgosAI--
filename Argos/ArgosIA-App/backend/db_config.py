"""Configuración segura de conexión con Turso.

Las credenciales solo se leen del entorno o de un archivo .env local que no se
incluye en el paquete. Ningún error de configuración imprime la URL o el token.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit

import libsql_client
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class DatabaseConfigurationError(RuntimeError):
    """Falta la configuración local necesaria para conectarse a Turso."""


class DatabaseUnavailableError(RuntimeError):
    """Turso no respondió o no se pudo abrir el cliente."""


def get_app_dir() -> Path:
    """Directorio que contiene la aplicación o el ejecutable empaquetado."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def _load_local_environment() -> None:
    explicit_env = os.getenv("ARGOS_ENV_FILE")
    if explicit_env:
        candidates = [Path(explicit_env)]
    else:
        app_dir = get_app_dir()
        candidates = [app_dir / ".env"]
        if getattr(sys, "frozen", False):
            candidates.append(app_dir.parent / ".env")
    local_app_data = os.getenv("LOCALAPPDATA")
    if local_app_data:
        candidates.append(Path(local_app_data) / "ArgosIA" / ".env")

    for candidate in candidates:
        try:
            if candidate.is_file():
                load_dotenv(candidate, override=False)
                if os.getenv("TURSO_DATABASE_URL") and os.getenv("TURSO_AUTH_TOKEN"):
                    return
        except OSError:
            logger.warning("No se pudo leer el archivo local de configuración de ArgosIA.")


def _get_database_settings() -> tuple[str, str]:
    _load_local_environment()
    url = (os.getenv("TURSO_DATABASE_URL") or "").strip()
    token = (os.getenv("TURSO_AUTH_TOKEN") or "").strip()

    if not url or not token:
        raise DatabaseConfigurationError(
            "Falta la configuración local de Turso. Definí TURSO_DATABASE_URL y "
            "TURSO_AUTH_TOKEN en el entorno o en el archivo .env local."
        )

    try:
        parsed = urlsplit(url)
        hostname = (parsed.hostname or "").lower()
    except ValueError:
        raise DatabaseConfigurationError(
            "La dirección configurada para Turso no tiene un formato válido."
        ) from None

    secure_turso_url = parsed.scheme.lower() == "libsql" and (
        hostname.endswith(".turso.io") or hostname == "localhost"
    )
    if not secure_turso_url or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise DatabaseConfigurationError(
            "Usá la URL libsql:// de Turso, sin token ni credenciales dentro de la dirección."
        )

    return url, token


def obtener_cliente_turso():
    """Abre libSQL por HTTPS para evitar el handshake WebSocket heredado."""
    url, token = _get_database_settings()
    try:
        parsed = urlsplit(url)
        # libsql:// se interpreta como WSS en libsql-client. La API HTTP de
        # Turso usa el mismo host autenticado mediante HTTPS.
        http_url = parsed._replace(scheme="https").geturl()
        return libsql_client.create_client(url=http_url, auth_token=token)
    except Exception as exc:
        logger.warning("No se pudo inicializar el cliente de Turso (%s).", type(exc).__name__)
        raise DatabaseUnavailableError(
            "No se pudo iniciar la conexión con Turso. Revisá la red y la configuración local."
        ) from None
