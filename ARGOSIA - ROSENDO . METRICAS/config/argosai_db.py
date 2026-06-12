import sqlite3
from datetime import datetime

DB_NAME = "ARGOSAI.db"

def inicializar_base_argosai():
    """Crea la estructura de tablas y triggers en el archivo .db"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Activar soporte de claves foráneas
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # 1. CREACIÓN DE TODAS LAS TABLAS
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS usuario(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        email TEXT,
        contrasenia TEXT,
        telefono TEXT
    );

    CREATE TABLE IF NOT EXISTS camara(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ubicacion TEXT,
        estado TEXT,
        direccionIP TEXT
    );

    CREATE TABLE IF NOT EXISTS video(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ruta TEXT,
        fecha TEXT, 
        duracion TEXT, 
        tamanoArchivo REAL,
        tiempoLimite TEXT, 
        camara_id INTEGER,
        FOREIGN KEY (camara_id) REFERENCES camara(id) 
    );

    CREATE TABLE IF NOT EXISTS rol_empleado(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombreRol TEXT,
        descripcion TEXT
    );

    CREATE TABLE IF NOT EXISTS empleado(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        genero TEXT,
        rendimiento REAL,
        estado TEXT,
        urlImagen TEXT,
        rol_id INTEGER,
        FOREIGN KEY (rol_id) REFERENCES rol_empleado(id)
    );

    CREATE TABLE IF NOT EXISTS diasSemana(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dia TEXT
    );

    CREATE TABLE IF NOT EXISTS turno(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        HoraInicio TEXT,
        HoraFin TEXT,
        empleado_id INTEGER,
        FOREIGN KEY (empleado_id) REFERENCES empleado(id)
    );

    CREATE TABLE IF NOT EXISTS diasTurno(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        turno_id INTEGER,
        diaSemana_id INTEGER,
        FOREIGN KEY (turno_id) REFERENCES turno(id),
        FOREIGN KEY (diaSemana_id) REFERENCES diasSemana(id)
    );

    CREATE TABLE IF NOT EXISTS horas(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fechaYHoraEntrada TEXT, 
        fechaYHoraSalida TEXT,
        empleado_id INTEGER,
        FOREIGN KEY (empleado_id) REFERENCES empleado(id)
    );

    CREATE TABLE IF NOT EXISTS horas_extra(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cantidad REAL,
        horas_id INTEGER,
        FOREIGN KEY (horas_id) REFERENCES horas(id)
    );

    CREATE TABLE IF NOT EXISTS actividad(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipoActividad TEXT,
        fechaYHoraComienzo TEXT,
        fechaYHoraFin TEXT,
        empleado_id INTEGER,
        FOREIGN KEY (empleado_id) REFERENCES empleado(id)
    );

    CREATE TABLE IF NOT EXISTS metrica(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT
    );

    CREATE TABLE IF NOT EXISTS inforMetrica(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        actividad_id INTEGER,
        metrica_id INTEGER,
        FOREIGN KEY (actividad_id) REFERENCES actividad(id),
        FOREIGN KEY (metrica_id) REFERENCES metrica(id)
    );

    CREATE TABLE IF NOT EXISTS alerta(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        grado TEXT,
        incumplimiento TEXT,
        fechaYHora TEXT,
        empleado_id INTEGER,
        FOREIGN KEY (empleado_id) REFERENCES empleado(id)
    );

    CREATE TABLE IF NOT EXISTS highlights(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        minutoInicio TEXT,
        minutoFin TEXT,
        video_id INTEGER,
        actividad_id INTEGER,
        FOREIGN KEY (video_id) REFERENCES video(id),
        FOREIGN KEY (actividad_id) REFERENCES actividad(id)
    );

    CREATE TABLE IF NOT EXISTS revision_alerta(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        estadoRevision TEXT,
        comentarios TEXT,
        fechaYHoraRevision TEXT,
        usuario_id INTEGER,
        alerta_id INTEGER,
        FOREIGN KEY (usuario_id) REFERENCES usuario(id),
        FOREIGN KEY (alerta_id) REFERENCES alerta(id)
    );

    CREATE TABLE IF NOT EXISTS mov_sospechoso(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        minutoInicio TEXT,
        minutoFin TEXT,
        descripcionPersonaInvolucrada TEXT,
        boundingBox TEXT,
        video_id INTEGER,
        FOREIGN KEY (video_id) REFERENCES video(id)
    );

    CREATE TABLE IF NOT EXISTS auditoria(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        accion TEXT,
        usuario_id INTEGER,
        tablaM TEXT,
        registro_afectado_id INTEGER,
        fecha TEXT,
        FOREIGN KEY (usuario_id) REFERENCES usuario(id)
    );
    """)

    # 2. CREACIÓN DINÁMICA DE TRIGGERS DE AUDITORÍA
    # SQLite usa un disparador por tabla. Usamos CURRENT_TIMESTAMP para la fecha.
    tablas_auditadas = [
        'rol_empleado', 'empleado', 'turno', 'horas', 'horas_extra', 
        'actividad', 'metrica', 'alerta', 'camara', 'video', 
        'highlights', 'mov_sospechoso', 'revision_alerta', 'usuario'
    ]

    for tabla in tablas_auditadas:
        cursor.execute(f"""
        CREATE TRIGGER IF NOT EXISTS trg_after_insert_{tabla} AFTER INSERT ON {tabla}
        BEGIN
            INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
            VALUES ('INSERT', NULL, '{tabla}', NEW.id, datetime('now', 'localtime'));
        END;
        """)
        
        cursor.execute(f"""
        CREATE TRIGGER IF NOT EXISTS trg_after_update_{tabla} AFTER UPDATE ON {tabla}
        BEGIN
            INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
            VALUES ('UPDATE', NULL, '{tabla}', NEW.id, datetime('now', 'localtime'));
        END;
        """)
        
        cursor.execute(f"""
        CREATE TRIGGER IF NOT EXISTS trg_after_delete_{tabla} AFTER DELETE ON {tabla}
        BEGIN
            INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
            VALUES ('DELETE', NULL, '{tabla}', OLD.id, datetime('now', 'localtime'));
        END;
        """)

    conn.commit()
    conn.close()
    print("[+] Base de datos ARGOSAI y Triggers inicializados con éxito.")


# =====================================================================
# TRADUCCIÓN DE STORED PROCEDURES A FUNCIONES DE PYTHON (SQLITE)
# =====================================================================

def ejecutar_transaccion(query, parametros, msg_exito, usuario_id=None, tabla_m=None, accion=None):
    """Función auxiliar para reutilizar la lógica de manejo de excepciones y transacciones."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    try:
        cursor.execute(query, parametros)
        id_afectado = cursor.lastrowid if accion == 'INSERT' else (parametros[0] if parametros else None)
        
        # Como SQLite no tiene variables globales de sesión para los triggers,
        # si se pasa un usuario_id, forzamos la auditoría real acá de forma manual:
        if usuario_id and tabla_m and accion and id_afectado:
            cursor.execute("""
                INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
                VALUES (?, ?, ?, ?, datetime('now', 'localtime'))
            """, (accion, usuario_id, tabla_m, id_afectado))
            
        conn.commit()
        return msg_exito
    except sqlite3.Error as e:
        conn.rollback()
        return f"Ocurrio un error: {e}"
    finally:
        conn.close()

# --- Usuarios ---
def cu(nombre, email, contrasenia, telefono):
    """Crear Usuario"""
    return ejecutar_transaccion(
        "INSERT INTO usuario(nombre, email, contrasenia, telefono) VALUES(?, ?, ?, ?);",
        (nombre, email, contrasenia, telefono), "Usuario creado con éxito."
    )

# --- Cámaras ---
def gc(ubicacion, estado, direccionIP, usuario_id=None):
    """Guardar Cámara"""
    return ejecutar_transaccion(
        "INSERT INTO camara(ubicacion, estado, direccionIP) VALUES(?, ?, ?);",
        (ubicacion, estado, direccionIP), "Cámara guardada con éxito.", usuario_id, 'camara', 'INSERT'
    )

def vtc():
    """Ver todas las cámaras"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM camara;")
        resultados = cursor.fetchall()
        return resultados, "Mostrando cámaras.."
    except sqlite3.Error:
        return [], "Ocurrio un error."
    finally:
        conn.close()

def vdc(id_camara):
    """Ver datos de una cámara"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM camara WHERE id = ?;", (id_camara,))
        resultado = cursor.fetchone()
        return resultado, f"Mostrando datos de la cámara con el id {id_camara}."
    except sqlite3.Error:
        return None, "Ocurrio un error."
    finally:
        conn.close()

def bc(id_camara, usuario_id=None):
    """Borrar Cámara"""
    return ejecutar_transaccion(
        "DELETE FROM camara WHERE id = ?;", (id_camara,), 
        "Cámara borrada con éxito.", usuario_id, 'camara', 'DELETE'
    )

def mc(id_camara, ubicacion, estado, direccionIP, usuario_id=None):
    """Modificar Cámara"""
    return ejecutar_transaccion(
        "UPDATE camara SET ubicacion = ?, estado = ?, direccionIP = ? WHERE id = ?;",
        (ubicacion, estado, direccionIP, id_camara), "Cámara modificada con éxito.", usuario_id, 'camara', 'UPDATE'
    )

# --- Videos ---
def gv(ruta, fecha, duracion, tamanoArchivo, tiempoLimite, camara_id, usuario_id=None):
    """Guardar Video"""
    return ejecutar_transaccion(
        "INSERT INTO video(ruta, fecha, duracion, tamanoArchivo, tiempoLimite, camara_id) VALUES(?, ?, ?, ?, ?, ?);",
        (ruta, fecha, duracion, tamanoArchivo, tiempoLimite, camara_id), "Video guardado con éxito.", usuario_id, 'video', 'INSERT'
    )

def mv():
    """Mostrar Videos"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM video;")
        return cursor.fetchall(), "Mostrando videos..."
    except sqlite3.Error:
        return [], "Ocurrio un error."
    finally:
        conn.close()

def bv(id_video, usuario_id=None):
    """Borrar Video"""
    return ejecutar_transaccion(
        "DELETE FROM video WHERE id = ?;", (id_video,), "Video borrado con éxito", usuario_id, 'video', 'DELETE'
    )

# --- Empleados ---
def ce(nombre, genero, rendimiento, estado, urlImagen, id_rol, usuario_id=None):
    """Crear Empleado"""
    return ejecutar_transaccion(
        "INSERT INTO empleado(nombre, genero, rendimiento, estado, urlImagen, rol_id) VALUES(?, ?, ?, ?, ?, ?);",
        (nombre, genero, rendimiento, estado, urlImagen, id_rol), "Empleado guardado con éxito.", usuario_id, 'empleado', 'INSERT'
    )

def be(id_empleado, usuario_id=None):
    """Borrar Empleado"""
    return ejecutar_transaccion(
        "DELETE FROM empleado WHERE id = ?;", (id_empleado,), "Empleado borrado con éxito.", usuario_id, 'empleado', 'DELETE'
    )

def me(id_empleado, nombre, genero, rendimiento, estado, urlImagen, id_rol, usuario_id=None):
    """Modificar Empleado"""
    return ejecutar_transaccion(
        "UPDATE empleado SET nombre = ?, genero = ?, rendimiento = ?, estado = ?, urlImagen = ?, rol_id = ? WHERE id = ?;",
        (nombre, genero, rendimiento, estado, urlImagen, id_rol, id_empleado), "Datos del empleado actualizados con éxito.", usuario_id, 'empleado', 'UPDATE'
    )

# --- Turnos ---
def ct(HoraInicio, HoraFin, id_empleado, usuario_id=None):
    """Crear Turno"""
    return ejecutar_transaccion(
        "INSERT INTO turno(HoraInicio, HoraFin, empleado_id) VALUES(?, ?, ?);",
        (HoraInicio, HoraFin, id_empleado), "Turno del empleado asignado con éxito.", usuario_id, 'turno', 'INSERT'
    )

def gdt(id_turno, id_diaSemana):
    """Guardar Días de un Turno"""
    return ejecutar_transaccion(
        "INSERT INTO diasTurno(turno_id, diaSemana_id) VALUES(?, ?);",
        (id_turno, id_diaSemana), "Diás de turnos del empleado asignado con éxito."
    )
	
def bt(id_turno, usuario_id=None):
    """Borrar Turno"""
    return ejecutar_transaccion(
        "DELETE FROM turno WHERE id = ?;", (id_turno,), "Turno del empleado eliminado con éxito.", usuario_id, 'turno', 'DELETE'
    )
 
def mt():
    """Mostrar Turnos"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM turno;")
        return cursor.fetchall(), "Mostrando todos los turnos..."
    except sqlite3.Error:
        return [], "Ocurrio un error."
    finally:
        conn.close()

def mte(id_empleado):
    """Mostrar Turnos de Empleado"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM turno WHERE empleado_id = ?;", (id_empleado,))
        return cursor.fetchall(), "Mostrando todos los turnos del empleado seleccionado..."
    except sqlite3.Error:
        return [], "Ocurrio un error."
    finally:
        conn.close()

# --- Horas y Horas Extra ---
def gh(fechaYHoraEntrada, fechaYHoraSalida, id_empleado, usuario_id=None):
    """Guardar Horas"""
    return ejecutar_transaccion(
        "INSERT INTO horas(fechaYHoraEntrada, fechaYHoraSalida, empleado_id) VALUES(?, ?, ?);",
        (fechaYHoraEntrada, fechaYHoraSalida, id_empleado), "Horas guardadas con éxito", usuario_id, 'horas', 'INSERT'
    )

def vhef(id_empleado, fecha):
    """Ver Horas de un Empleado en una Fecha"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        # Usamos la función DATE() de SQLite para comparar strings con formato ISO
        cursor.execute("SELECT * FROM horas WHERE empleado_id = ? AND DATE(fechaYHoraEntrada) = ?;", (id_empleado, fecha))
        return cursor.fetchall(), "Mostrando las horas del empleado seleccionado en el día seleccionado..."
    except sqlite3.Error:
        return [], "Ocurrio un error."
    finally:
        conn.close()

def ghe(cantidad, id_horas, usuario_id=None):
    """Guardar Horas Extra"""
    return ejecutar_transaccion(
        "INSERT INTO horas_extra(cantidad, horas_id) VALUES(?, ?);",
        (cantidad, id_horas), "Horas extra guardadas con éxito.", usuario_id, 'horas_extra', 'INSERT'
    )

# --- Actividades y Métricas ---
def ga(tipoActividad, fechaYHoraComienzo, fechaYHoraFin, id_empleado, usuario_id=None):
    """Guardar Actividad"""
    return ejecutar_transaccion(
        "INSERT INTO actividad(tipoActividad, fechaYHoraComienzo, fechaYHoraFin, empleado_id) VALUES(?, ?, ?, ?);",
        (tipoActividad, fechaYHoraComienzo, fechaYHoraFin, id_empleado), "Actividad guardada con éxito.", usuario_id, 'actividad', 'INSERT'
    )

def ba(id_actividad, usuario_id=None):
    """Borrar Actividad"""
    return ejecutar_transaccion(
        "DELETE FROM actividad WHERE id = ?;", (id_actividad,), "Actividad Borrada.", usuario_id, 'actividad', 'DELETE'
    )

def cm(tipo, usuario_id=None):
    """Crear Métrica"""
    return ejecutar_transaccion(
        "INSERT INTO metrica(tipo) VALUES(?);", (tipo,), "Metrica guardada con éxito.", usuario_id, 'metrica', 'INSERT'
    )

def cdm(id_actividad, id_metrica):
    """Cargar Datos de una Métrica (Relacional inforMetrica)"""
    return ejecutar_transaccion(
        "INSERT INTO inforMetrica(actividad_id, metrica_id) VALUES(?, ?);",
        (id_actividad, id_metrica), "Dato añadido a la métrica con éxito."
    )

# --- Alertas y Revisiones ---
def gal(grado, incumplimiento, fechaYHora, id_empleado, usuario_id=None):
    """Guardar Alerta"""
    return ejecutar_transaccion(
        "INSERT INTO alerta(grado, incumplimiento, fechaYHora, empleado_id) VALUES(?, ?, ?, ?);",
        (grado, incumplimiento, fechaYHora, id_empleado), "Alerta guardada con éxito.", usuario_id, 'alerta', 'INSERT'
    )

def bal(id_alerta, usuario_id=None):
    """Borrar Alerta"""
    return ejecutar_transaccion(
        "DELETE FROM alerta WHERE id = ?;", (id_alerta,), "Alerta guardada con éxito.", usuario_id, 'alerta', 'DELETE'
    )

def cra(estadoRevision, comentarios, fechaYHoraRevision, id_usuario, id_alerta, usuario_id=None):
    """Crear una Revisión de Alerta"""
    return ejecutar_transaccion(
        "INSERT INTO revision_alerta(estadoRevision, comentarios, fechaYHoraRevision, usuario_id, alerta_id) VALUES(?, ?, ?, ?, ?);",
        (estadoRevision, comentarios, fechaYHoraRevision, id_usuario, id_alerta), "Revisión de alerta creada con éxito.", usuario_id, 'revision_alerta', 'INSERT'
    )

def mera(id_revision, estadoRevision, usuario_id=None):
    """Modificar el Estado de una Revisión de Alerta"""
    return ejecutar_transaccion(
        "UPDATE revision_alerta SET estadoRevision = ? WHERE id = ?;",
        (estadoRevision, id_revision), "Estado de la revisión modificado con éxito.", usuario_id, 'revision_alerta', 'UPDATE'
    )

# --- Highlights y Movimientos Sospechosos ---
def ghi(minutoInicio, minutoFin, id_video, id_actividad, usuario_id=None):
    """Guardar Highlight"""
    return ejecutar_transaccion(
        "INSERT INTO highlights(minutoInicio, minutoFin, video_id, actividad_id) VALUES(?, ?, ?, ?);",
        (minutoInicio, minutoFin, id_video, id_actividad), "Highlight guardado con éxito.", usuario_id, 'highlights', 'INSERT'
    )

def bhi(id_highlight, usuario_id=None):
    """Borrar Highlight"""
    return ejecutar_transaccion(
        "DELETE FROM highlights WHERE id = ?;", (id_highlight,), "Highlight guardado con éxito.", usuario_id, 'highlights', 'DELETE'
    )

def gms(minutoInicio, minutoFin, descripcionPersonaInvolucrada, boundingBox, id_video, usuario_id=None):
    """Guardar un movimiento sospechoso"""
    return ejecutar_transaccion(
        "INSERT INTO mov_sospechoso(minutoInicio, minutoFin, descripcionPersonaInvolucrada, boundingBox, video_id) VALUES(?, ?, ?, ?, ?);",
        (minutoInicio, minutoFin, descripcionPersonaInvolucrada, boundingBox, id_video), "Movimiento sospechoso registrado con éxito.", usuario_id, 'mov_sospechoso', 'INSERT'
    )

def bms(id_movimiento, usuario_id=None):
    """Borrar un movimiento sospechoso"""
    return ejecutar_transaccion(
        "DELETE FROM mov_sospechoso WHERE id = ?;", (id_movimiento,), "Movimiento sospechoso registrado con éxito.", usuario_id, 'mov_sospechoso', 'DELETE'
    )
def cargar_empleados_iniciales():
    conn = sqlite3.connect("config/ARGOSAI.db") # Asegurate que la ruta sea esta
    cursor = conn.cursor()
    
    # Verificamos si ya hay empleados para no duplicar
    cursor.execute("SELECT COUNT(*) FROM empleado")
    if cursor.fetchone()[0] == 0:
        print("[*] La tabla empleado está vacía. Cargando datos de prueba...")
        empleados = [
            ("Rosendo", "M", 0.95, "Activo", "foto1.jpg", 1),
            ("Krawzyck", "M", 0.90, "Activo", "foto2.jpg", 1),
            ("Thiago", "M", 0.85, "Activo", "foto3.jpg", 1)
        ]
        cursor.executemany("INSERT INTO empleado(nombre, genero, rendimiento, estado, urlImagen, rol_id) VALUES(?,?,?,?,?,?)", empleados)
        conn.commit()
    conn.close()


    

# Test rápido de inicialización
if __name__ == "__main__":
    inicializar_base_argosai()
    cargar_empleados_iniciales() # 