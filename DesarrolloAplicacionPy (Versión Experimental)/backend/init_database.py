import sys
import os
import logging
import asyncio
from pathlib import Path

# ============================================================
# INYECTOR DE RUTAS DINÁMICO
# ============================================================
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from backend.db_config import obtener_cliente_turso

# Configuración estricta del Pilar de Registros (Logging)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Buscamos el archivo de respaldo de estructura dentro de backend/models/
# 🟢 MEJORA: Definimos una ruta limpia y flexible que busca el archivo .sql
MODEL_DIR = Path(__file__).resolve().parent / "models"
SQL_FILE_PATH = MODEL_DIR / "schema.sql"  # <-- Te sugiero renombrar tu archivo a 'schema.sql'

# Si aún conserva el nombre anterior, usamos este respaldo de compatibilidad
if not SQL_FILE_PATH.exists():
    SQL_FILE_PATH = MODEL_DIR / "DB ArgosAi (1).sql"

async def inicializar_estructura_base_datos():
    logging.info("Iniciando el proceso de construcción de tablas en Turso Cloud...")
    
    if not SQL_FILE_PATH.exists():
        logging.critical(f"No se encontró el archivo de estructura SQL en la ruta: {SQL_FILE_PATH}")
        sys.exit("❌ Error: Falta el archivo de respaldo estructural .sql para iniciar.")
        
    logging.info(f"Leyendo archivo de esquema relacional: {SQL_FILE_PATH.name}")
    with open(SQL_FILE_PATH, "r", encoding="utf-8") as f:
        contenido_sql = f.read()

    # Dividimos el archivo por puntos y comas para limpiar comandos individuales
    # Filtramos líneas vacías o comentarios de SQL corporativos
    comandos_crudos = contenido_sql.split(";")
    lote_comandos = []
    
    for comando in comandos_crudos:
        limpio = comando.strip()
        if limpio and not limpio.startswith("--") and not limpio.startswith("/*"):
            lote_comandos.append(limpio)

    if not lote_comandos:
        logging.warning("El archivo SQL no contiene comandos válidos para ejecutar.")
        return

    client = obtener_cliente_turso()
    try:
        logging.info(f"Enviando lote atómico de {len(lote_comandos)} sentencias relacionales (Garantizando ACID)...")
        
        # 🟢 PILAR TRANSACCIONES ACID: Inyección en bloque masivo
        # Turso aplica el lote completo de forma atómica; si una clave foránea o tabla falla, revierte todo
        await client.batch(lote_comandos)
        logging.info("¡Estructura relacional e integridad de tablas creadas con éxito total en la nube!")
        
    except Exception as e_sql:
        # 🟢 PILAR MANEJO DE ERRORES: Captura explícita, fin al silenciamiento de excepciones
        logging.error(f"Fallo crítico al inyectar el esquema relacional. Operación abortada (ROLLBACK): {e_sql}")
        logging.error("Revise la sintaxis de sus sentencias SQL o la compatibilidad de tipos con libSQL.")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(inicializar_estructura_base_datos())
