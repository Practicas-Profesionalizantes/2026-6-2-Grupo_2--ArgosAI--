@echo off
setlocal
cd /d "%~dp0"

call "%~dp0prepararEntorno.bat"
if errorlevel 1 (
    pause
    exit /b 1
)

"%ARGOS_PY%" "%~dp0scripts\verificar_esquema.py"
set "ARGOS_EXIT=%errorlevel%"
echo.
pause
exit /b %ARGOS_EXIT%
