"""Lanzador de escritorio sin depender de Chrome ni de una pestaña externa."""

from __future__ import annotations

import os
import queue
import socket
import sys
import subprocess
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path


class AppStartupError(RuntimeError):
    """Error de arranque seguro para mostrar en la ventana de escritorio."""


def _resource_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parent


def _startup_log_path() -> Path:
    try:
        app_dir = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "ArgosIA"
        app_dir.mkdir(parents=True, exist_ok=True)
        return app_dir / "launch.log"
    except Exception:
        return _resource_root() / "argos_launch.log"


def _log_startup(message: str) -> None:
    try:
        path = _startup_log_path()
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with path.open("a", encoding="utf-8") as log_file:
            log_file.write(f"[{timestamp}] {message}\n")
    except Exception:
        pass


def _show_startup_dialog(message: str) -> None:
    try:
        from PySide6.QtWidgets import QApplication, QMessageBox

        app = QApplication.instance() or QApplication(sys.argv[:1])
        QMessageBox.critical(None, "ArgosIA no pudo iniciar", message)
    except Exception:
        try:
            import ctypes

            ctypes.windll.user32.MessageBoxW(None, message, "ArgosIA no pudo iniciar", 0x10)
        except Exception:
            print(f"ArgosIA no pudo iniciar: {message}", file=sys.stderr)


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _streamlit_worker(script_path: Path, port: int) -> None:
    """Proceso hijo: Streamlit corre en su hilo principal y no abre un navegador."""
    # An installation-wide Streamlit config may enable developmentMode. It
    # conflicts with the dynamically selected local port used by this app.
    os.environ["STREAMLIT_GLOBAL_DEVELOPMENT_MODE"] = "false"
    from streamlit.web.cli import main as streamlit_cli

    sys.argv = [
        "streamlit",
        "run",
        str(script_path),
        "--global.developmentMode=false",
        "--server.headless=true",
        "--server.address=127.0.0.1",
        f"--server.port={port}",
        "--server.enableXsrfProtection=true",
        "--server.fileWatcherType=none",
        "--server.maxUploadSize=200",
        "--browser.gatherUsageStats=false",
    ]
    streamlit_cli()


def _start_streamlit(script_path: Path, port: int) -> subprocess.Popen:
    if getattr(sys, "frozen", False):
        command = [sys.executable, "--argos-streamlit-worker", str(script_path), str(port)]
    else:
        command = [sys.executable, str(Path(__file__).resolve()), "--argos-streamlit-worker", str(script_path), str(port)]
    creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0
    return subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creation_flags,
        close_fds=True,
    )


def _start_media_server(port: int) -> subprocess.Popen:
    """Uvicorn captura señales del sistema y por eso debe correr en proceso propio."""
    if getattr(sys, "frozen", False):
        command = [sys.executable, "--argos-media-worker", str(port)]
    else:
        command = [sys.executable, str(Path(__file__).resolve()), "--argos-media-worker", str(port)]
    creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0
    return subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creation_flags,
        close_fds=True,
    )


def _audit_worker(errors: queue.Queue) -> None:
    try:
        import asyncio
        from backend.auditoria_inactividad import main_loop

        asyncio.run(main_loop())
    except BaseException as exc:
        errors.put(type(exc).__name__)


def _wait_for_streamlit(port: int, process: subprocess.Popen, errors: queue.Queue, timeout: float = 45.0) -> None:
    deadline = time.monotonic() + timeout
    url = f"http://127.0.0.1:{port}/_stcore/health"
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise AppStartupError(
                "Streamlit se cerró antes de mostrar la interfaz. Revisá la instalación local y volvé a iniciar."
            )
        if not errors.empty():
            kind = errors.get_nowait()
            raise AppStartupError(f"No se pudo iniciar el servidor local ({kind}).") from None
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except (OSError, urllib.error.URLError):
            time.sleep(0.25)
    raise TimeoutError("La interfaz no respondió dentro del tiempo esperado.")


def _wait_for_media_server(port: int, process: subprocess.Popen, timeout: float = 20.0) -> None:
    deadline = time.monotonic() + timeout
    url = f"http://127.0.0.1:{port}/health"
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise AppStartupError("No se pudo iniciar el servidor local de clips. Reiniciá ArgosIA e intentá otra vez.")
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 204:
                    return
        except (OSError, urllib.error.URLError):
            time.sleep(0.2)
    raise AppStartupError("El servidor local de clips no respondió. Reiniciá ArgosIA e intentá otra vez.")


def _stop_process(process: subprocess.Popen | None) -> None:
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()


def iniciar_app_escritorio() -> int:
    _log_startup("Iniciando ArgosIA")
    root = _resource_root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    script_path = root / "frontend" / "app.py"
    if not script_path.is_file():
        raise FileNotFoundError("No se encontró la interfaz de ArgosIA dentro del paquete.")

    # El token nunca se incorpora al ejecutable; la configuración se lee en el equipo del usuario.
    from backend.db_config import get_app_dir
    from backend.storage import get_data_dir, media_directory
    from dotenv import load_dotenv

    app_dir = get_app_dir()
    env_path = app_dir / ".env"
    if env_path.is_file():
        load_dotenv(env_path, override=False)
    get_data_dir().mkdir(parents=True, exist_ok=True)
    media_directory().mkdir(parents=True, exist_ok=True)

    ui_port = _free_port()
    media_port = _free_port()
    while media_port == ui_port:
        media_port = _free_port()
    os.environ["ARGOS_MEDIA_PORT"] = str(media_port)
    os.environ["ARGOS_MEDIA_BASE_URL"] = f"http://127.0.0.1:{media_port}"
    os.environ["FRONTEND_ORIGIN"] = f"http://127.0.0.1:{ui_port}"
    os.environ.update(
        {
            "STREAMLIT_GLOBAL_DEVELOPMENT_MODE": "false",
            "STREAMLIT_SERVER_HEADLESS": "true",
            "STREAMLIT_SERVER_ADDRESS": "127.0.0.1",
            "STREAMLIT_SERVER_PORT": str(ui_port),
            "STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION": "true",
            "STREAMLIT_SERVER_FILE_WATCHER_TYPE": "none",
            "STREAMLIT_SERVER_MAX_UPLOAD_SIZE": "200",
            "STREAMLIT_BROWSER_GATHER_USAGE_STATS": "false",
        }
    )

    errors: queue.Queue = queue.Queue()
    media_process = _start_media_server(media_port)
    streamlit_process = None
    try:
        _wait_for_media_server(media_port, media_process)
        if os.getenv("ARGOS_ENABLE_AUDIT_WORKER", "false").strip().casefold() in {"1", "true", "yes", "si"}:
            threading.Thread(target=_audit_worker, args=(errors,), daemon=True, name="argos-audit").start()
        streamlit_process = _start_streamlit(script_path, ui_port)
        _wait_for_streamlit(ui_port, streamlit_process, errors)
        from PySide6.QtCore import QUrl
        from PySide6.QtWidgets import QApplication, QMainWindow
        from PySide6.QtWebEngineWidgets import QWebEngineView

        app = QApplication(sys.argv[:1])
        app.setApplicationName("ArgosIA")
        window = QMainWindow()
        window.setWindowTitle("ArgosIA · Gestión de Heladería")
        window.resize(1360, 900)
        window.setMinimumSize(980, 680)
        view = QWebEngineView(window)
        view.setUrl(QUrl(f"http://127.0.0.1:{ui_port}"))
        window.setCentralWidget(view)
        window.show()
        return app.exec()
    finally:
        _stop_process(streamlit_process)
        _stop_process(media_process)


if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "--argos-streamlit-worker":
        _streamlit_worker(Path(sys.argv[2]), int(sys.argv[3]))
        raise SystemExit(0)
    if len(sys.argv) >= 3 and sys.argv[1] == "--argos-media-worker":
        import uvicorn
        from backend.server_media import app

        uvicorn.run(app, host="127.0.0.1", port=int(sys.argv[2]), log_level="error", access_log=False)
        raise SystemExit(0)
    try:
        raise SystemExit(iniciar_app_escritorio())
    except Exception as exc:
        # No se muestran trazas, URLs ni configuración a la persona usuaria.
        message = (
            str(exc)
            if isinstance(exc, (AppStartupError, FileNotFoundError, TimeoutError))
            else "Ocurrió un error al iniciar los componentes locales. Revisá la instalación y volvé a intentar."
        )
        _log_startup(f"Error de arranque: {message}")
        _show_startup_dialog(message)
        raise SystemExit(1) from None
