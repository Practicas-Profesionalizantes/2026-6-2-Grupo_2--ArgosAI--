@echo off
setlocal
cd /d "%~dp0"

echo [ArgosIA] Preparando el entorno local...
call "%~dp0prepararEntorno.bat"
if errorlevel 1 (
    echo [ArgosIA] ERROR: no se pudo preparar el entorno.
    pause
    exit /b 1
)

echo [ArgosIA] Iniciando la aplicación...
"%ARGOS_PY%" "%~dp0main.py"
set "ARGOS_EXIT=%errorlevel%"
if not "%ARGOS_EXIT%"=="0" (
    echo [ArgosIA] La aplicación cerró con código %ARGOS_EXIT%.
    pause
)
exit /b %ARGOS_EXIT%
