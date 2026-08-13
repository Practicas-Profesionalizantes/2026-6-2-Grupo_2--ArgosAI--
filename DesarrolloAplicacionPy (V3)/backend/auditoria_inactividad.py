import sys
from pathlib import Path

# ============================================================
# INYECTOR DE RUTAS DINÁMICO
# ============================================================
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

import asyncio
import datetime
from backend.SPs import guardar_alerta, obtener_cliente_turso

MINUTOS_TOLERANCIA_INACTIVIDAD = 15 

def mapear_dia_semana_espanol(numero_dia_python):
    dias = {0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves", 4: "Viernes", 5: "Sábado", 6: "Domingo"}
    return dias.get(numero_dia_python)

async def verificar_inactividad_tiempo_real():
    ahora = datetime.datetime.now()
    hora_actual = ahora.strftime("%H:%M:%S")
    dia_actual_nombre = mapear_dia_semana_espanol(ahora.weekday())
    
    print(f"[{ahora}] [Auditoría de Local] Escaneando inactividad en la heladería...")
    
    client = obtener_cliente_turso()
    try:
        query_empleados = """
            SELECT e.id, e.nombre FROM empleado e
            INNER JOIN turno t ON e.id = t.empleado_id
            INNER JOIN diasTurno dt ON t.id = dt.turno_id
            INNER JOIN diasSemana ds ON dt.diaSemana_id = ds.id
            WHERE ds.dia = ? AND ? BETWEEN t.HoraInicio AND t.HoraFin AND e.estado = 'Activo';
        """
        # 🟢 CORREGIDO: Se agrega 'await' para esperar la respuesta de Turso
        resultado_emp = await client.execute(query_empleados, [dia_actual_nombre, hora_actual])
        
        for fila in resultado_emp.rows:
            emp_id = fila[0]
            emp_nombre = fila[1]
            
            tiempo_limite = ahora - datetime.timedelta(minutes=MINUTOS_TOLERANCIA_INACTIVIDAD)
            tiempo_limite_str = tiempo_limite.strftime("%Y-%m-%d %H:%M:%S")
            
            query_actividad = "SELECT COUNT(*) FROM actividad WHERE empleado_id = ? AND fechaYHoraComienzo >= ?;"
            # 🟢 CORREGIDO: Se agrega 'await'
            resultado_act = await client.execute(query_actividad, [emp_id, tiempo_limite_str])
            
            cant_actividades = resultado_act.rows[0][0] if resultado_act.rows else 0
            
            if cant_actividades == 0:
                print(f"⚠️ [ALERTA] El empleado {emp_nombre} (ID: {emp_id}) se encuentra inactivo.")
                desc = f"Inactividad crítica detectada por IA mayor a {MINUTOS_TOLERANCIA_INACTIVIDAD} minutos."
                # 🟢 CORREGIDO: Se agrega 'await' para la subida asíncrona
                await guardar_alerta(grado="Alto", incumplimiento=desc, empleado_id=emp_id)
            else:
                print(f"✅ [OK] Empleado {emp_nombre} verificado en actividad continua.")
                
    except Exception as e:
        print(f"❌ Error en el bucle analítico de auditoría: {e}")
    finally:
        # 🟢 CORREGIDO: El cierre del cliente en Turso también es asíncrono
        await client.close()

async def main_loop():
    try:
        while True:
            # 🟢 CORREGIDO: Se agrega 'await' mandatorio
            await verificar_inactividad_tiempo_real()
            await asyncio.sleep(60)
    except asyncio.CancelledError:
        pass

if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("[-] Motor de auditoría de inactividad detenido por el usuario.")
