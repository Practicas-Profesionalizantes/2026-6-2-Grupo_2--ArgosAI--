import os
import subprocess
import sys

def iniciar_app_escritorio():
    # 1. Ruta de tu archivo de interfaz de Streamlit
    script_path = "app.py"
    
    # 2. Comando para arrancar Streamlit en segundo plano sin abrir pestañas comunes
    # Usamos sys.executable para asegurarnos de llamar al Python correcto del sistema
    comando = [
        sys.executable, "-m", "streamlit", "run", script_path,
        "--server.headless", "true",
        "--server.port", "8501"
    ]
    
    # Iniciamos el servidor de Streamlit de forma silenciosa
    subprocess.Popen(comando, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    # 3. Forzamos a abrir la interfaz en una ventana nativa limpia (Modo App de Chrome/Edge)
    # Esto elimina las barras de navegación, historial y pestañas para simular un software clásico
    url = "http://localhost:8501"
    if sys.platform == "win32":
        os.system(f'start chrome --app={url}')
    elif sys.platform == "darwin": # Mac
        os.system(f'open -a "Google Chrome" --args --app={url}')

if __name__ == "__main__":
    iniciar_app_escritorio()