@echo off
setlocal
cd /d "%~dp0"

call "%~dp0prepararEntorno.bat"
if errorlevel 1 (
    pause
    exit /b 1
)

"%ARGOS_PY%" "%~dp0main.py"
set "ARGOS_EXIT=%errorlevel%"
if not "%ARGOS_EXIT%"=="0" pause
exit /b %ARGOS_EXIT%
