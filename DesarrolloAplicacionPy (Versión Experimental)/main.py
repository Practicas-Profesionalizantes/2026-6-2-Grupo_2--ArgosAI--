import subprocess
import sys
import time
import os

def iniciar_ecosistema_argos():
    print("[INFO] Lanzando el entorno unificado de ArgosIA (Python 3.13)...")

    # 1. Servidor de archivos estáticos para reproducir los videos de la IA
    print("[INFO] Encendiendo servidor de videos en puerto 8000...")
    subprocess.Popen([sys.executable, "backend/server_media.py"], stdout=subprocess.DEVNULL)
    time.sleep(1)

    # 2. Daemon de auditoría de inactividad de Rosendo
    print("[INFO] Encendiendo motor de auditoría en segundo plano...")
    subprocess.Popen([sys.executable, "backend/auditoria_inactividad.py"])
    time.sleep(1)

    # 3. Interfaz central reactiva de Streamlit
    print("[INFO] Inicializando panel de Streamlit en puerto 8501...")
    comando_frontend = [
        sys.executable, "-m", "streamlit", "run", "frontend/app.py",
        "--server.headless", "true", "--server.port", "8501"
    ]
    subprocess.Popen(comando_frontend, stdout=subprocess.DEVNULL)
    time.sleep(3)

    # 4. Modo aplicación nativa de escritorio sin barras de navegación
    url = "http://localhost:8501"
    if sys.platform == "win32":
        os.system(f'start chrome --app={url}')
    elif sys.platform == "darwin":
        os.system(f'open -a "Google Chrome" --args --app={url}')

if __name__ == "__main__":
    iniciar_ecosistema_argos()
