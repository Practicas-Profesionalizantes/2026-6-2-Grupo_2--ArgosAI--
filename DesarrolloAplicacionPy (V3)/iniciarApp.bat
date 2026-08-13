@echo off
title Lanzador ArgosIA - Modo Unificado Remoto
cd /d "%~dp0"

:: Mata cualquier proceso colgado previo para limpiar puertos
taskkill /f /im python.exe >nul 2>&1

:: Dispara el entorno virtual y arranca el orquestador
call .venv\Scripts\activate
python main.py
exit
