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
import datetime

# Importamos la configuración y funciones de la capa de datos de Turso
from backend.db_config import obtener_cliente_turso
from backend.SPs import guardar_alerta

# Configuración estricta del Pilar de Registros (Logging)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

MINUTOS_TOLERANCIA_INACTIVIDAD = 15 

def mapear_dia_semana_espanol(numero_dia_python):
    dias = {0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves", 4: "Viernes", 5: "Sábado", 6: "Domingo"}
    return dias.get(numero_dia_python)

async def verificar_inactividad_tiempo_real():
    ahora = datetime.datetime.now()
    hora_actual = ahora.strftime("%H:%M:%S")
    dia_actual_nombre = mapear_dia_semana_espanol(ahora.weekday())
    
    logging.info("Escaneando inactividad operativa en la heladería...")
    
    client = obtener_cliente_turso()
    try:
        # Buscamos empleados activos en su horario de turno
        query_empleados = """
            SELECT e.id, e.nombre FROM empleado e
            INNER JOIN turno t ON e.id = t.empleado_id
            INNER JOIN diasTurno dt ON t.id = dt.turno_id
            INNER JOIN diasSemana ds ON dt.diaSemana_id = ds.id
            WHERE ds.dia = ? AND ? BETWEEN t.HoraInicio AND t.HoraFin AND e.estado = 'Activo';
        """
        resultado_emp = await client.execute(query_empleados, [dia_actual_nombre, hora_actual])
        
        for fila in resultado_emp.rows:
            emp_id = fila[0]
            emp_nombre = fila[1]
            
            # 🟢 PILAR MANEJO DE ERRORES: Aislamiento individual por empleado
            try:
                tiempo_limite = ahora - datetime.timedelta(minutes=MINUTOS_TOLERANCIA_INACTIVIDAD)
                tiempo_limite_str = tiempo_limite.strftime("%Y-%m-%d %H:%M:%S")
                
                query_actividad = "SELECT COUNT(*) FROM actividad WHERE empleado_id = ? AND fechaYHoraComienzo >= ?;"
                resultado_act = await client.execute(query_actividad, [emp_id, tiempo_limite_str])
                
                cant_actividades = resultado_act.rows[0][0] if resultado_act.rows else 0
                
                if cant_actividades == 0:
                    logging.warning(f"Inactividad crítica detectada para {emp_nombre} (ID: {emp_id}).")
                    desc = f"Inactividad en tiempo real mayor a {MINUTOS_TOLERANCIA_INACTIVIDAD} minutos."
                    
                    # Se delega a la función asíncrona de SPs, pasando un ID operador de sistema (ej: 1)
                    await guardar_alerta(grado="Alta", incumplimiento=desc, empleado_id=emp_id)
                else:
                    logging.info(f"Empleado {emp_nombre} verificado en actividad continua.")
                    
            except Exception as e_empleado:
                # Si falla este empleado, capturamos el error y el bucle sigue con los demás
                logging.error(f"Fallo al auditar al empleado ID {emp_id} ({emp_nombre}): {e_empleado}")
                continue
                
    except Exception as e_global:
        logging.error(f"Error general en la ronda de auditoría de red: {e_global}")
    finally:
        await client.close()

async def main_loop():
    try:
        while True:
            await verificar_inactividad_tiempo_real()
            await asyncio.sleep(60)
    except asyncio.CancelledError:
        pass

if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        logging.info("Motor de auditoría de inactividad apagado por el operador.")
