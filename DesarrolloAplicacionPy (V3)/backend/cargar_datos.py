import sys
from pathlib import Path
import logging

# ============================================================
# INYECTOR DE RUTAS DINÁMICO
# ============================================================
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

import asyncio
from backend.db_config import obtener_cliente_turso

# Configuración estricta del Pilar de Registros (Logging)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

async def cargar_datos_semilla_produccion():
    logging.info("Iniciando conexión con el clúster de Turso Cloud para carga masiva...")
    client = obtener_cliente_turso()
    
    try:
        logging.info("Abriendo lote transaccional atómico (Garantizando ACID)...")
        
        # En Turso/libSQL ejecutamos un lote atómico (Batch). Todo se aplica o nada.
        # Primero limpiamos tablas para evitar duplicados, respetando integridad
        operaciones = [
            # Limpieza en orden inverso por claves foráneas
            "DELETE FROM alerta;",
            "DELETE FROM actividad;",
            "DELETE FROM horas_extra;",
            "DELETE FROM horas;",
            "DELETE FROM diasTurno;",
            "DELETE FROM turno;",
            "DELETE FROM empleado;",
            "DELETE FROM rol_empleado;",
            "DELETE FROM diasSemana;",
            "DELETE FROM usuario;",
            
            # 1. Inserción de data en la tabla diasSemana (Parametrizado con Prepared Statements)
            libsql_client.InArgs("INSERT INTO diasSemana (dia) VALUES (?);", ["Lunes"]),
            libsql_client.InArgs("INSERT INTO diasSemana (dia) VALUES (?);", ["Martes"]),
            libsql_client.InArgs("INSERT INTO diasSemana (dia) VALUES (?);", ["Miércoles"]),
            libsql_client.InArgs("INSERT INTO diasSemana (dia) VALUES (?);", ["Jueves"]),
            libsql_client.InArgs("INSERT INTO diasSemana (dia) VALUES (?);", ["Viernes"]),
            libsql_client.InArgs("INSERT INTO diasSemana (dia) VALUES (?);", ["Sábado"]),
            libsql_client.InArgs("INSERT INTO diasSemana (dia) VALUES (?);", ["Domingo"]),
            
            # 2. Inserción de data en la tabla rol_empleado
            libsql_client.InArgs("INSERT INTO rol_empleado (id, nombreRol, descripcion) VALUES (?, ?, ?);", 
                                 [1, "Administrativo", "Tareas generales de oficina y supervisión"]),
            libsql_client.InArgs("INSERT INTO rol_empleado (id, nombreRol, descripcion) VALUES (?, ?, ?);", 
                                 [2, "Operario", "Línea de producción y despacho de helados"]),
            
            # 3. Inserción de Usuarios Administrativos Semilla (Con hash pre-calculado de forma segura)
            # Clave para ambos: "admin2026" -> Hasheada con SHA-256
            libsql_client.InArgs("INSERT INTO usuario (id, nombre, email, contrasenia, telefono) VALUES (?, ?, ?, ?, ?);",
                                 [1, "Control Argos", "admin@argosai.com", "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918", "+541187654321"]),
            # Cuenta para Pablo con clave "pedraza123" -> Hasheada con SHA-256
            libsql_client.InArgs("INSERT INTO usuario (id, nombre, email, contrasenia, telefono) VALUES (?, ?, ?, ?, ?);",
                                 [2, "Pablo Pedraza", "pablo@argosai.com", "f19e42c222ff47e62bbdb9fb66d6d371cfb96b4bf200d705c93c3dc8ef6f0cd9", "+541112345678"]),
            
            # 4. Inserción de Empleados de prueba de la heladería
            libsql_client.InArgs("INSERT INTO empleado (id, nombre, genero, rendimiento, estado, urlImagen, rol_id) VALUES (?, ?, ?, ?, ?, ?, ?);",
                                 [1, "Rosendo García", "Masculino", 95.0, "Activo", "data/biometria/emp_1", 2]),
            libsql_client.InArgs("INSERT INTO empleado (id, nombre, genero, rendimiento, estado, urlImagen, rol_id) VALUES (?, ?, ?, ?, ?, ?, ?);",
                                 [2, "Ana Martínez", "Femenino", 92.5, "Activo", "data/biometria/emp_2", 2]),
            
            # 5. Configuración de Turnos de ejemplo
            libsql_client.InArgs("INSERT INTO turno (id, HoraInicio, HoraFin, DescansoInicio, DescansoFin, empleado_id) VALUES (?, ?, ?, ?, ?, ?);",
                                 [101, "08:00:00", "17:00:00", "12:00:00", "13:00:00", 1]),
            libsql_client.InArgs("INSERT INTO turno (id, HoraInicio, HoraFin, DescansoInicio, DescansoFin, empleado_id) VALUES (?, ?, ?, ?, ?, ?);",
                                 [102, "14:00:00", "22:00:00", "18:00:00", "19:00:00", 2]),
                                 
            # 6. Vinculación de Días a los Turnos (Días de la semana id: 1=Lunes, 2=Martes, etc.)
            libsql_client.InArgs("INSERT INTO diasTurno (turno_id, diaSemana_id) VALUES (?, ?);", [101, 1]),
            libsql_client.InArgs("INSERT INTO diasTurno (turno_id, diaSemana_id) VALUES (?, ?);", [101, 2]),
            libsql_client.InArgs("INSERT INTO diasTurno (turno_id, diaSemana_id) VALUES (?, ?);", [102, 3]),
            libsql_client.InArgs("INSERT INTO diasTurno (turno_id, diaSemana_id) VALUES (?, ?);", [102, 4]),
            
            # 7. Inserción de fichadas de Horas y Horas Extra de ejemplo para pruebas de analíticas
            libsql_client.InArgs("INSERT INTO horas (id, fechaYHoraEntrada, fechaYHoraSalida, empleado_id) VALUES (?, ?, ?, ?);",
                                 [501, "2026-08-18 08:00:00", "2026-08-18 19:30:00", 1]),
            libsql_client.InArgs("INSERT INTO horas_extra (cantidad, horas_id) VALUES (?, ?);", 
                                 [1.5, 501])
        ]
        
        # Ejecución del bloque completo en una sola transacción transoceánica
        import libsql_client
        await client.batch(operaciones)
        logging.info("¡Datos semilla impactados y guardados con éxito total (COMMIT completo)!")
        
    except Exception as e:
        # Si algo falla en la mitad, la transacción en Turso no se aplica (Bailout de seguridad)
        logging.error(f"Fallo crítico en la carga masiva. Operación abortada (ROLLBACK automático): {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(cargar_datos_semilla_produccion())
