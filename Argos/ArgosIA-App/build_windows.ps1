$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $root

$pythonLauncher = Get-Command py -ErrorAction SilentlyContinue
$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonLauncher -and -not $pythonCommand) {
    throw 'No se encontró Python en la computadora usada para compilar.'
}

$localAppData = if ($env:LOCALAPPDATA) { $env:LOCALAPPDATA } else { Join-Path $env:USERPROFILE 'AppData\Local' }
$builderEnvironment = Join-Path $localAppData 'AIA'
$builder = Join-Path $builderEnvironment 'Scripts\python.exe'
if (-not (Test-Path -LiteralPath $builder)) {
    if ($pythonLauncher) {
        & $pythonLauncher.Source -3 -m venv $builderEnvironment
    } else {
        & $pythonCommand.Source -m venv $builderEnvironment
    }
    if ($LASTEXITCODE -ne 0) {
        throw 'No se pudo crear el entorno de compilación.'
    }
}
if (-not (Test-Path -LiteralPath $builder)) {
    throw 'No se pudo crear el entorno de compilación.'
}

$dependencyCheckCode = @'
import importlib
import sys
try:
    modules = ('streamlit', 'pandas', 'PIL', 'libsql_client', 'dotenv', 'fastapi', 'uvicorn', 'PySide6', 'imageio_ffmpeg', 'PyInstaller')
    for module in modules:
        importlib.import_module(module)
    if importlib.import_module('streamlit').__version__ != '1.65.0':
        sys.exit(1)
except Exception:
    sys.exit(1)
'@
$dependencyCheck = & $builder -c $dependencyCheckCode 2>&1
$dependencyCheckExitCode = $LASTEXITCODE
if ($dependencyCheckExitCode -ne 0) {
    Write-Host 'Faltan dependencias o hay una versión incompatible; preparando el entorno de compilación...'
    & $builder -m pip install --disable-pip-version-check -r (Join-Path $root 'requirements.txt')
    if ($LASTEXITCODE -ne 0) {
        throw 'Falló la instalación de dependencias. No se inició el empaquetado.'
    }
}

$workPath = Join-Path $localAppData 'AIA-Build'
$distributionPath = Join-Path $root 'dist'
$specPath = Join-Path $root 'build-spec'
$frontendPath = Join-Path $root 'frontend'
if (-not (Test-Path -LiteralPath $frontendPath -PathType Container)) {
    throw "No se encontró la carpeta frontend: $frontendPath"
}
New-Item -ItemType Directory -Force -Path $workPath, $distributionPath, $specPath | Out-Null

$pyinstallerArguments = @(
    '-m', 'PyInstaller',
    '--noconfirm', '--clean', '--onefile', '--windowed',
    '--name', 'ArgosIA',
    '--workpath', $workPath,
    '--distpath', $distributionPath,
    '--specpath', $specPath,
    '--collect-all', 'streamlit',
    '--collect-data', 'pandas',
    '--collect-all', 'PIL',
    '--collect-all', 'fastapi',
    '--collect-all', 'uvicorn',
    '--collect-all', 'PySide6',
    '--collect-all', 'shiboken6',
'--collect-all', 'imageio_ffmpeg',
    '--hidden-import', 'backend.SPs',
    '--hidden-import', 'backend.schema',
    '--hidden-import', 'backend.storage',
    '--hidden-import', 'backend.server_media',
    '--hidden-import', 'backend.auditoria_inactividad',
    '--hidden-import', 'frontend.panels',
    '--hidden-import', 'dotenv',
    '--add-data', "$frontendPath;frontend",
    (Join-Path $root 'main.py')
)
& $builder @pyinstallerArguments
if ($LASTEXITCODE -ne 0) {
    throw 'PyInstaller terminó con un error. Revisa el mensaje anterior; no se generó un EXE utilizable.'
}

$exe = Join-Path $root 'dist\ArgosIA.exe'
if (-not (Test-Path -LiteralPath $exe)) {
    throw 'PyInstaller no generó el ejecutable esperado.'
}
Write-Host "Ejecutable generado: $exe"
Write-Host 'Copiá .env.example como .env junto al EXE y configurá la conexión de Turso localmente.'
