@echo off
rem Prepara una sola vez el entorno de desarrollo en una ruta corta de AppData.
rem Esto evita el límite de rutas de Windows al instalar Qt/PySide6.

set "ARGOS_ROOT=%~dp0"
if not defined LOCALAPPDATA set "LOCALAPPDATA=%USERPROFILE%\AppData\Local"
set "ARGOS_VENV=%LOCALAPPDATA%\AIA"
set "ARGOS_PY=%ARGOS_VENV%\Scripts\python.exe"

if exist "%ARGOS_PY%" goto check_dependencies

set "ARGOS_BOOTSTRAP_PY="
where py >nul 2>&1
if errorlevel 1 goto try_python_command
for /f "delims=" %%P in ('py -3 -c "import sys; print(sys.executable)" 2^>nul') do set "ARGOS_BOOTSTRAP_PY=%%P"
if defined ARGOS_BOOTSTRAP_PY goto create_venv

:try_python_command
where python >nul 2>&1
if errorlevel 1 goto python_missing
for /f "delims=" %%P in ('python -c "import sys; print(sys.executable)" 2^>nul') do set "ARGOS_BOOTSTRAP_PY=%%P"
if not defined ARGOS_BOOTSTRAP_PY goto python_missing

:create_venv
if not exist "%ARGOS_VENV%" mkdir "%ARGOS_VENV%"
"%ARGOS_BOOTSTRAP_PY%" -m venv "%ARGOS_VENV%"
if errorlevel 1 goto venv_failed
if not exist "%ARGOS_PY%" goto venv_failed

:check_dependencies
"%ARGOS_PY%" -c "import streamlit, pandas, PIL, libsql_client, dotenv, fastapi, uvicorn, PySide6; assert streamlit.__version__ == '1.65.0'" >nul 2>&1
if not errorlevel 1 exit /b 0

echo Instalando o reparando las dependencias de ArgosIA. Esto puede tardar unos minutos...
"%ARGOS_PY%" -m pip install --disable-pip-version-check -r "%ARGOS_ROOT%requirements.txt"
if errorlevel 1 goto install_failed
exit /b 0

:python_missing
echo No se encontro Python. Para ejecutar desde el codigo hace falta Python; el EXE final no lo necesitara.
exit /b 1

:venv_failed
echo No se pudo crear el entorno de ArgosIA en "%ARGOS_VENV%".
exit /b 1

:install_failed
echo No se pudieron instalar las dependencias. Revisa la conexion a internet y vuelve a ejecutar este archivo.
exit /b 1
