import sqlite3
import hashlib

def inicializar_base_de_datos():
    # Al conectarse a este archivo, si no existe, SQLite lo crea en el acto
    conexion = sqlite3.connect("argosai.db")
    cursor = conexion.cursor()
    
    # Crear tabla de usuario (Sintaxis compatible con SQLite)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuario(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        contrasenia TEXT NOT NULL,
        telefono TEXT
    );
    """)
    
    # Insertar usuarios de prueba si la tabla está vacía
    cursor.execute("SELECT COUNT(*) FROM usuario")
    if cursor.fetchone()[0] == 0:
        # password123 en SHA-256
        pass1 = hashlib.sha256("password123".encode('utf-8')).hexdigest()
        pass2 = hashlib.sha256("admin2026".encode('utf-8')).hexdigest()
        
        usuarios = [
            ('Martín Romero', 'martin@argosai.com', pass1, '+541112345678'),
            ('Control Argos', 'admin@argosai.com', pass2, '+541187654321')
        ]
        cursor.executemany("""
        INSERT INTO usuario(nombre, email, contrasenia, telefono) 
        VALUES (?, ?, ?, ?);
        """, usuarios)
        conexion.commit()
        print("Base de datos 'argosai.db' creada e inicializada con éxito.")
    
    conexion.close()

if __name__ == "__main__":
    inicializar_base_de_datos()