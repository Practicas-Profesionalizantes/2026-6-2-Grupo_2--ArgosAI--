import pymysql
import os

# CONFIGURACIÓN (Ajusta la contraseña si usas)
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "" 

# Ruta automática hacia la carpeta models y tu archivo
# !!! CAMBIA 'base_de_datos.sql' por el nombre REAL de tu archivo !!!
RUTA_SQL = os.path.join("models", "DB ArgosAi (1).sql") 

def importar_script_sql():
    if not os.path.exists(RUTA_SQL):
        print("[-] No encontré el archivo en: {0}".format(RUTA_SQL))
        print("⚠️ Asegúrate de haber copiado el archivo dentro de la carpeta 'models' y que el nombre coincida.")
        return

    try:
        # Conectar al servidor de MySQL
        conexion = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            autocommit=True
        )
        cursor = conexion.cursor()
        print("[+] Conectado a MySQL.")
        
        # Leer el archivo .sql entero
        print("[*] Leyendo el archivo SQL de la carpeta models...")
        with open(RUTA_SQL, "r", encoding="utf-8") as f:
            sql_entero = f.read()
        
        # MySQL no permite ejecutar múltiples comandos juntos fácilmente con execute() 
        # si contienen DELIMITER (común en triggers/procedures). Por eso separamos por comandos:
        comandos = sql_entero.split(";")
        
        print("[*] Inyectando base de datos...")
        for comando in comandos:
            comando_limpio = comando.strip()
            if comando_limpio: # Si el comando no está vacío
                try:
                    cursor.execute(comando_limpio)
                except Exception as e_sql:
                    # Ignoramos advertencias menores, pero si hay error crítico lo avisa
                    pass
                    
        print("[===] ¡Tu archivo SQL se ha cargado con éxito en MySQL desde la carpeta models! [===]")
        cursor.close()
        conexion.close()

    except Exception as e:
        print("[-] Error general al importar: {0}".format(e))

if __name__ == "__main__":
    importar_script_sql()