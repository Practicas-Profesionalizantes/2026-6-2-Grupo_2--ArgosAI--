import datetime
import time
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
# CONFIGURACIÓN DE LA BASE DE DATOS
# Opción A: Si usas XAMPP (Sin contraseña, nota los dos puntos ':@')
DATABASE_URL = "mysql+pymysql://root:@localhost:3306/ARGOSAI"

# Opción B: Si usas MySQL nativo con una contraseña (ej: admin123) cambiala acá:
DATABASE_URL = "mysql+pymysql://root:@localhost:3306/ARGOSAI"

# ESTA ES LA LÍNEA QUE TE FALTA (Crear el motor de conexión)
engine = create_engine(DATABASE_URL)

# Creamos la sesión usando ese engine
Session = sessionmaker(bind=engine)
session = Session()
MINUTOS_TOLERANCIA_INACTIVIDAD = 15 

def mapear_dia_semana_espanol(numero_dia_python):
    # En Python 3.6 el .weekday() funciona igual (0=Lunes, 6=Domingo)
    dias = {
        0: "Lunes", 1: "Martes", 2: "Miércoles", 
        3: "Jueves", 4: "Viernes", 5: "Sábado", 6: "Domingo"
    }
    return dias.get(numero_dia_python)

def verificar_inactividad_tiempo_real():
    ahora = datetime.datetime.now()
    hora_actual = ahora.strftime("%H:%M:%S")
    dia_actual_nombre = mapear_dia_semana_espanol(ahora.weekday())
    
    print("[{0}] Ejecutando control: {1} - {2}".format(ahora, dia_actual_nombre, hora_actual))
    
    # Query compatible con SQLAlchemy para Python 3.6
    query_empleados_activos = text("""
        SELECT e.id AS empleado_id, e.nombre 
        FROM empleado e
        INNER JOIN turno t ON e.id = t.empleado_id
        INNER JOIN diasTurno dt ON t.id = dt.turno_id
        INNER JOIN diasSemana ds ON dt.diaSemana_id = ds.id
        WHERE ds.dia = :dia_actual
          AND :hora_actual BETWEEN t.HoraInicio AND t.HoraFin
          AND e.estado = 'Activo';
    """)
    
    try:
        empleados_en_turno = session.execute(
            query_empleados_activos, 
            {"dia_actual": dia_actual_nombre, "hora_actual": hora_actual}
        ).fetchall()
        
        for emp in empleados_en_turno:
            emp_id = emp.empleado_id
            emp_nombre = emp.nombre
            
            # Restamos los minutos de tolerancia de forma segura
            tiempo_limite_actividad = ahora - datetime.timedelta(minutes=MINUTOS_TOLERANCIA_INACTIVIDAD)
            
            # Formateamos la fecha a string para evitar conflictos de types entre Python 3.6 y MySQL
            tiempo_limite_str = tiempo_limite_actividad.strftime("%Y-%m-%d %H:%M:%S")
            
            query_actividad_reciente = text("""
                SELECT COUNT(*) FROM actividad
                WHERE empleado_id = :empleado_id
                  AND fechaYHoraComienzo >= :tiempo_limite;
            """)
            
            cant_actividades = session.execute(
                query_actividad_reciente, 
                {"empleado_id": emp_id, "tiempo_limite": tiempo_limite_str}
            ).scalar()
            
            if cant_actividades == 0:
                print("⚠️ ALERTA: {0} (ID: {1}) no trabaja hace {2} min.".format(emp_nombre, emp_id, MINUTOS_TOLERANCIA_INACTIVIDAD))
                
                incumplimiento_descripcion = "Inactividad en tiempo real mayor a " + str(MINUTOS_TOLERANCIA_INACTIVIDAD) + " minutos."
                fecha_alerta_str = ahora.strftime("%Y-%m-%d %H:%M:%S")
                
                # Seteamos la variable de sesión requerida por tus Triggers de Auditoría
                session.execute(text("SET @current_user_id = 1;")) 
                
                # Llamada al Stored Procedure 'gal'
                sp_query = text("""
                    CALL gal(:grado, :incumplimiento, :fecha, :empleado_id, @mensaje_out);
                """)
                
                session.execute(sp_query, {
                    "grado": "Alto",
                    "incumplimiento": incumplimiento_descripcion,
                    "fecha": fecha_alerta_str,
                    "empleado_id": emp_id
                })
                session.commit()
                
                msg_out = session.execute(text("SELECT @mensaje_out;")).scalar()
                print("📌 BD: {0}".format(msg_out))
            else:
                print("✅ Empleado {0} en actividad.".format(emp_nombre))
                
    except Exception as e:
        session.rollback()
        print("❌ Error en Python 3.6: {0}".format(e))
    finally:
        session.close()

if __name__ == "__main__":
    # Bucle de simulación en tiempo real (revisa cada 60 segundos)
    try:
        while True:
            verificar_inactividad_tiempo_real()
            time.sleep(60)
    except KeyboardInterrupt:
        print("Monitor ArgosAI detenido por el usuario.")