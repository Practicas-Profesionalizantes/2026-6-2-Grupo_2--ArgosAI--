# database/connection.py
import sqlite3
import os
import hashlib

DATABASE_PATH = "argosai.db"
BIOMETRIA_ROOT = os.path.join("data", "biometria")

def obtener_conexion():
    conexion = sqlite3.connect(DATABASE_PATH)
    conexion.execute("PRAGMA foreign_keys = ON;")
    conexion.row_factory = sqlite3.Row
    return conexion

def registrar_auditoria(cursor, accion, usuario_id, tabla, registro_id):
    query = """
        INSERT INTO auditoria (accion, usuario_id, tablaM, registro_affected_id, fecha)
        VALUES (?, ?, ?, ?, datetime('now', 'localtime'));
    """
    cursor.execute(query, (accion, usuario_id, tabla, registro_id))

def inicializar_todo():
    os.makedirs(BIOMETRIA_ROOT, exist_ok=True)
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
    # --- CREACIÓN DE TABLAS ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuario(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        contrasenia TEXT NOT NULL,
        telefono TEXT
    );""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rol_empleado(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombreRol TEXT UNIQUE,
        descripcion TEXT
    );""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS empleado(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        genero TEXT,
        rendimiento REAL,
        estado TEXT,
        urlImagen TEXT, 
        rol_id INTEGER,
        FOREIGN KEY (rol_id) REFERENCES rol_empleado(id) ON DELETE SET NULL
    );""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS diasSemana(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dia TEXT UNIQUE
    );""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS turno(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        HoraInicio TEXT,
        HoraFin TEXT,
        DescansoInicio TEXT,
        DescansoFin TEXT,
        empleado_id INTEGER,
        FOREIGN KEY (empleado_id) REFERENCES empleado(id) ON DELETE CASCADE
    );""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS diasTurno(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        turno_id INTEGER,
        diaSemana_id INTEGER,
        FOREIGN KEY (turno_id) REFERENCES turno(id) ON DELETE CASCADE,
        FOREIGN KEY (diaSemana_id) REFERENCES diasSemana(id)
    );""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS horas(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fechaYHoraEntrada TEXT,
        fechaYHoraSalida TEXT,
        empleado_id INTEGER,
        FOREIGN KEY (empleado_id) REFERENCES empleado(id) ON DELETE CASCADE
    );""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS horas_extra(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cantidad REAL,
        horas_id INTEGER,
        FOREIGN KEY (horas_id) REFERENCES horas(id) ON DELETE CASCADE
    );""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS auditoria(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        accion TEXT,
        usuario_id INTEGER,
        tablaM TEXT,
        registro_affected_id INTEGER,
        fecha TEXT,
        FOREIGN KEY (usuario_id) REFERENCES usuario(id)
    );""")

    # --- MIGRACIÓN DEFENSIVA (Por si la DB ya existía sin los campos de descanso) ---
    try:
        cursor.execute("ALTER TABLE turno ADD COLUMN DescansoInicio TEXT;")
        cursor.execute("ALTER TABLE turno ADD COLUMN DescansoFin TEXT;")
    except sqlite3.OperationalError:
        pass  # Las columnas ya existen

    # --- INSERCIÓN DE DATA SEMILLA ---
    cursor.execute("SELECT COUNT(*) FROM diasSemana")
    if cursor.fetchone()[0] == 0:
        dias = [('Lunes',), ('Martes',), ('Miércoles',), ('Jueves',), ('Viernes',), ('Sábado',), ('Domingo',)]
        cursor.executemany("INSERT INTO diasSemana (dia) VALUES (?);", dias)

    cursor.execute("SELECT COUNT(*) FROM rol_empleado")
    if cursor.fetchone()[0] == 0:
        roles = [('Administrativo', 'Tareas generales de oficina'), ('Operario', 'Línea de producción')]
        cursor.executemany("INSERT INTO rol_empleado (nombreRol, descripcion) VALUES (?, ?);", roles)

    cursor.execute("SELECT COUNT(*) FROM usuario")
    if cursor.fetchone()[0] == 0:
        pass1 = hashlib.sha256("password123".encode('utf-8')).hexdigest()
        pass2 = hashlib.sha256("admin2026".encode('utf-8')).hexdigest()
        usuarios = [
            ('Martín Romero', 'martin@argosai.com', pass1, '+541112345678'),
            ('Control Argos', 'admin@argosai.com', pass2, '+541187654321')
        ]
        cursor.executemany("INSERT INTO usuario(nombre, email, contrasenia, telefono) VALUES (?, ?, ?, ?);", usuarios)

    # --- GENERACIÓN DE ENTRADAS Y HORAS EXTRA GENÉRICAS PARA EL EMPLEADO ID 2 ---
    cursor.execute("SELECT COUNT(*) FROM empleado WHERE id = 2")
    if cursor.fetchone()[0] == 0:
        # Aseguramos la existencia del Empleado ID 2
        cursor.execute("""
            INSERT INTO empleado (id, nombre, genero, rendimiento, estado, urlImagen, rol_id) 
            VALUES (2, 'Carlos Pérez', 'Masculino', 92.5, 'Activo', 'data/biometria/emp_2', 2);
        """)
        
        # Insertar fichadas de horas y sus respectivas horas extra asociadas
        fichadas_falsas = [
            (101, '2026-06-08 08:00:00', '2026-06-08 19:30:00', 2), # 1.5 horas extra
            (102, '2026-06-09 08:00:00', '2026-06-09 21:00:00', 2), # 3.0 horas extra
            (103, '2026-06-10 08:00:00', '2026-06-10 18:45:00', 2)  # 0.75 horas extra
        ]
        cursor.executemany("INSERT INTO horas (id, fechaYHoraEntrada, fechaYHoraSalida, empleado_id) VALUES (?, ?, ?, ?);", fichadas_falsas)
        
        extras_falsas = [
            (1.5, 101),
            (3.0, 102),
            (0.75, 103)
        ]
        cursor.executemany("INSERT INTO horas_extra (cantidad, horas_id) VALUES (?, ?);", extras_falsas)

    conexion.commit()
    conexion.close()