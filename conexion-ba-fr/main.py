import os
import subprocess
import sys
import time

def iniciar_app_escritorio():
    print("[INFO] Iniciando el ecosistema ArgosIA...")

    # ============================================================
    # 1. ARRANCAR EL BACKEND (Python 3.6.8 - Usando 'py')
    # ============================================================
    # Cambiamos "python" por "py" para que sea compatible con tu sistema
    comando_backend = ["py", "con-back/app_backend.py"]
    
    print("[INFO] Encendiendo servidor Backend en puerto 5000...")
    subprocess.Popen(comando_backend, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Esperamos 2 segundos a que el backend levante el puerto 5000
    time.sleep(2)

    # ============================================================
    # 2. ARRANCAR EL FRONTEND (Streamlit - Usando 'py')
    # ============================================================
    script_frontend = "con-front/app-fr.py" 
    
    # Cambiamos "python" por "py" para que use tu entorno global con Streamlit
    comando_frontend = [
        "py", "-m", "streamlit", "run", script_frontend,
        "--server.headless", "true",
        "--server.port", "8501"
    ]
    
    print("[INFO] Encendiendo interfaz Frontend (Streamlit) en puerto 8501...")
    subprocess.Popen(comando_frontend, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Esperamos 3 segundos a que Streamlit termine de procesar la interfaz
    time.sleep(3)

    # ============================================================
    # 3. MODO APLICACIÓN ESCRITORIO (Chrome / Edge / Mac)
    # ============================================================
    url = "http://localhost:8501"
    print("[INFO] Abriendo ventana de escritorio dedicada...")
    
    if sys.platform == "win32":
        os.system(f'start chrome --app={url}')
    elif sys.platform == "darwin":  # Mac
        os.system(f'open -a "Google Chrome" --args --app={url}')
    else:  # Linux
        os.system(f'google-chrome --app={url}')

if __name__ == "__main__":
    iniciar_app_escritorio()
