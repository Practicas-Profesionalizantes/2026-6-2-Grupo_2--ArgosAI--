import pymysql
import datetime

# CONEXIÓN (Ajusta si usas contraseña en tu MySQL)
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = ""
DB_NAME = "ARGOSAI"

def insertar_multiples_empleados_y_alertas():
    try:
        conexion = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            autocommit=True
        )
        cursor = conexion.cursor()
        
        print("[*] Limpiando tablas para la nueva prueba masiva...")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        cursor.execute("TRUNCATE TABLE diasTurno;")
        cursor.execute("TRUNCATE TABLE turno;")
        cursor.execute("TRUNCATE TABLE diasSemana;")
        cursor.execute("TRUNCATE TABLE actividad;")
        cursor.execute("TRUNCATE TABLE empleado;")
        cursor.execute("TRUNCATE TABLE rol_empleado;")
        cursor.execute("TRUNCATE TABLE alerta;")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

        print("[*] Creando Roles...")
        cursor.execute("INSERT INTO rol_empleado (id, nombreRol, descripcion) VALUES (1, 'Operario de Planta', 'Monitoreo de empaque');")
        cursor.execute("INSERT INTO rol_empleado (id, nombreRol, descripcion) VALUES (2, 'Supervisor', 'Control de calidad y lineas');")

        print("[*] Insertando 3 Empleados distintos...")
        cursor.execute("INSERT INTO empleado (id, nombre, genero, rendimiento, estado, urlImagen, rol_id) VALUES (1, 'Rosendo Test', 'Masculino', 95.5, 'Activo', 'http://argosai.com', 1);")
        cursor.execute("INSERT INTO empleado (id, nombre, genero, rendimiento, estado, urlImagen, rol_id) VALUES (2, 'Laura Gomez', 'Femenino', 98.0, 'Activo', 'http://argosai.com', 1);")
        cursor.execute("INSERT INTO empleado (id, nombre, genero, rendimiento, estado, urlImagen, rol_id) VALUES (3, 'Carlos Perez', 'Masculino', 88.2, 'Activo', 'http://argosai.com', 2);")

        print("[*] Insertando Dias de la semana...")
        dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        for i, dia in enumerate(dias, start=1):
            cursor.execute("INSERT INTO diasSemana (id, dia) VALUES (%s, %s);", (i, dia))

        print("[*] Asignando Turnos a los 3 empleados para el dia de hoy...")
        # Se genera un rango completo para que coincida siempre con tu hora actual de prueba
        cursor.execute("INSERT INTO turno (id, HoraInicio, HoraFin, empleado_id) VALUES (1, '00:00:00', '23:59:00', 1);")
        cursor.execute("INSERT INTO turno (id, HoraInicio, HoraFin, empleado_id) VALUES (2, '00:00:00', '23:59:00', 2);")
        cursor.execute("INSERT INTO turno (id, HoraInicio, HoraFin, empleado_id) VALUES (3, '00:00:00', '23:59:00', 3);")
        
        # Enlazar automáticamente los 3 turnos al día Jueves (ID 4)
        cursor.execute("INSERT INTO diasTurno (id, turno_id, diaSemana_id) VALUES (1, 1, 4);")
        cursor.execute("INSERT INTO diasTurno (id, turno_id, diaSemana_id) VALUES (2, 2, 4);")
        cursor.execute("INSERT INTO diasTurno (id, turno_id, diaSemana_id) VALUES (3, 3, 4);")

        print("[*] Inyectando alertas identificadas por empleado...")
        ahora = datetime.datetime.now()
        hace_5_min = ahora - datetime.timedelta(minutes=5)
        hace_20_min = ahora - datetime.timedelta(minutes=20)
        
        # Alerta 1: Rosendo
        cursor.execute("""
            INSERT INTO alerta (id, grado, incumplimiento, fechaYHora, empleado_id) 
            VALUES (1, 'Alto', 'Inactividad prolongada en Linea de Empaque', %s, 1);
        """, (hace_20_min.strftime('%Y-%m-%d %H:%M:%S'),))

        # Alerta 2: Laura
        cursor.execute("""
            INSERT INTO alerta (id, grado, incumplimiento, fechaYHora, empleado_id) 
            VALUES (2, 'Medio', 'Uso de dispositivo movil en zona restringida', %s, 2);
        """, (hace_5_min.strftime('%Y-%m-%d %H:%M:%S'),))

        # Alerta 3: Carlos
        cursor.execute("""
            INSERT INTO alerta (id, grado, incumplimiento, fechaYHora, empleado_id) 
            VALUES (3, 'Critico', 'Abandono de puesto de control de seguridad', %s, 3);
        """, (ahora.strftime('%Y-%m-%d %H:%M:%S'),))

        print("[===] ¡Datos, MULTIPLES EMPLEADOS y ALERTAS cargados con exito! [===]")
        cursor.close()
        conexion.close()

    except Exception as e:
        print("[-] Error al guardar los datos en el lote masivo: {0}".format(e))

if __name__ == "__main__":
    insertar_multiples_empleados_y_alertas()