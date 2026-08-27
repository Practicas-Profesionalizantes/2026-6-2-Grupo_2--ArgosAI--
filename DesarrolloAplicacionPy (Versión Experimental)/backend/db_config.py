import os
import sys
import logging
from pathlib import Path
import libsql_client

# Configuración estricta del Pilar de Registros (Logging)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# 🟢 PILAR SEGURIDAD: Carga defensiva de variables de entorno desde el archivo .env
# Intentamos leer de forma directa; si no existen, buscamos leerlas de forma manual
TURSO_URL_RAW = os.getenv("TURSO_DATABASE_URL")
TURSO_TOKEN = os.getenv("TURSO_AUTH_TOKEN")

# Si las variables no están cargadas en el sistema operativo, leemos el archivo .env a mano
if not TURSO_URL_RAW or not TURSO_TOKEN:
    ruta_env = Path(__file__).resolve().parent.parent / ".env"
    if ruta_env.exists():
        with open(ruta_env, "r") as f:
            for linea in f:
                if "=" in linea and not linea.startswith("#"):
                    clave, valor = linea.strip().split("=", 1)
                    if clave == "TURSO_DATABASE_URL":
                        TURSO_URL_RAW = valor
                    elif clave == "TURSO_AUTH_TOKEN":
                        TURSO_TOKEN = valor

# Validación crítica de secretos antes de iniciar sockets
if not TURSO_URL_RAW or not TURSO_TOKEN:
    logging.critical("Falta configuración crítica en el entorno. No se encontraron las variables de Turso.")
    sys.exit("❌ Error: Configure las credenciales de Turso en su entorno o archivo .env")

# 🟢 SANEAMIENTO MATEMÁTICO AUTOMÁTICO DE URL
# Remueve de forma transparente cualquier prefijo redundante para evitar el recorte del subdominio de AWS
# 🟢 SANEAMIENTO DE URL: Mantener el protocolo nativo libsql://
HOST_LIMPIO = (
    TURSO_URL_RAW.replace("libsql://", "")
    .replace("https://", "")
    .replace("http://", "")
    .strip()
)
TURSO_URL = f"libsql://{HOST_LIMPIO}"

def obtener_cliente_turso():
  """Retorna el cliente oficial de Turso Cloud."""
  try:
    return libsql_client.create_client(url=TURSO_URL, auth_token=TURSO_TOKEN)
  except Exception as e_init:
    logging.error(
        f"Fallo crítico al instanciar el cliente de Turso Cloud: {e_init}"
    )
    raise e_init
