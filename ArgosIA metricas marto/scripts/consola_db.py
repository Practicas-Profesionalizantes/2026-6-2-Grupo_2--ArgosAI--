import sqlite3
import os

# Buscamos la base de datos en la carpeta config
db_path = os.path.join("config", "ARGOSAI.db")

# Conectamos
conexion = sqlite3.connect(db_path)
cursor = conexion.cursor()

try:
    print("Conectando a la base de datos...")
    
    # 1. Insertamos tres empleados de prueba
    # Nota: No incluimos 'id' porque suele ser AUTOINCREMENTAL (se genera solo)
    cursor.execute("""
        INSERT INTO empleados (nombre, rol, estado) 
        VALUES ('Rosendo García', 'Desarrollador', 'Activo')
    """)
    cursor.execute("""
        INSERT INTO empleados (nombre, rol, estado) 
        VALUES ('Ana Martínez', 'Analista de Datos', 'Activo')
    """)
    cursor.execute("""
        INSERT INTO empleados (nombre, rol, estado) 
        VALUES ('Carlos Pérez', 'Diseñador UI/UX', 'Inactivo')
    """)
    
    # IMPORTANTE: Guardar los cambios en el archivo .db
    conexion.commit()
    print("¡Registros guardados con éxito!")
    
    # 2. Hacemos el SELECT para comprobar que se agregaron correctamente
    cursor.execute("SELECT id, nombre, rol, estado FROM empleados")
    empleados = cursor.fetchall()
    
    print("\n=== LISTA DE EMPLEADOS EN LA BASE DE DATOS ===")
    for emp in empleados:
        print(f"ID: {emp[0]} | Nombre: {emp[1]} | Rol: {emp[2]} | Estado: {emp[3]}")
    print("==============================================")

except sqlite3.OperationalError as error:
    print("\n[ERROR] Ocurrió un problema con la base de datos:")
    print(f"Detalle: {error}")
    print("Verifica si el nombre de la tabla es 'empleados' o si las columnas coinciden.")

finally:
    # Cerramos la conexión siempre
    conexion.close()