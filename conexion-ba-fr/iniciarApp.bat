@echo off
title Cargando Panel Inteligente ArgosIA...

:: 1. Cerramos cualquier proceso previo colgado para liberar los puertos
taskkill /f /im python.exe >nul 2>&1

:: 2. Nos posicionamos de forma absoluta en la carpeta del proyecto (Cambiar esto segun la computadora) 
cd /d "C:\Users\Thiago\Desktop\DesarrolloAplicacionPy"

:: 3. Levantamos el servidor de la app de forma silenciosa y aislada
start /b python -m streamlit run app.py --server.headless true --server.port 8501

:: 4. Esperamos 4 segundos a que el motor analitico termine de encender
timeout /t 4 /nobreak >nul

:: 5. Forzamos la apertura en una ventana de aplicacion nativa dedicada de escritorio (Modo App)
start chrome --app=http://localhost:8501
exit