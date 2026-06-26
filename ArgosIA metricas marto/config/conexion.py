import sqlite3

DB_NAME = "ARGOSAI.db"

def ejecutar_lectura(query, parametros=()):
    """Sirve para SELECT. Devuelve los resultados o una lista vacía."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute(query, parametros)
        resultados = cursor.fetchall()
        return resultados
    except sqlite3.Error as e:
        print(f"Error de lectura: {e}")
        return []
    finally:
        conn.close()

def ejecutar_escritura(query, parametros=()):
    """Sirve para INSERT, UPDATE, DELETE. Devuelve True si salió bien."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    try:
        cursor.execute(query, parametros)
        conn.commit()
        return True
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Error de escritura: {e}")
        return False
    finally:
        conn.close()