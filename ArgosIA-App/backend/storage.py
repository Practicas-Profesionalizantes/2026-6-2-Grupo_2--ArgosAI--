"""Almacenamiento local de imágenes y clips con rutas confinadas."""

from __future__ import annotations

import io
import os
import re
import shutil
import sys
import subprocess
import uuid
import warnings
from pathlib import Path
from urllib.parse import quote

from PIL import Image, ImageOps

MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_BATCH_IMAGE_BYTES = 64 * 1024 * 1024
MAX_IMAGE_PIXELS = 40_000_000
MAX_IMAGES_PER_EMPLOYEE = 30
ALLOWED_FORMATS = {"JPEG": ".jpg", "PNG": ".png"}
MAX_VIDEO_BYTES = 200 * 1024 * 1024
ALLOWED_VIDEO_SUFFIXES = {".mp4", ".webm", ".mov"}


def get_app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def get_data_dir() -> Path:
    explicit = os.getenv("ARGOS_DATA_DIR")
    if explicit:
        configured = Path(explicit).expanduser()
        if not configured.is_absolute():
            configured = get_app_dir() / configured
        return configured.resolve()
    local = os.getenv("LOCALAPPDATA")
    if local:
        return (Path(local) / "ArgosIA").resolve()
    return (Path.home() / ".argosai").resolve()


def relative_employee_path(employee_id: int) -> str:
    return f"biometria/empleado_{int(employee_id)}"


def employee_photo_dir(employee_id: int, stored_path: str | None = None) -> Path:
    """Resuelve datos nuevos en AppData y acepta la carpeta legacy si está confinada."""
    employee_id = int(employee_id)
    app_dir = get_app_dir()
    legacy_root = (app_dir / "data" / "biometria").resolve()
    if stored_path:
        normalized = str(stored_path).replace("\\", "/").strip()
        candidate = (app_dir / normalized).resolve()
        try:
            candidate.relative_to(legacy_root)
            if candidate.is_dir():
                return candidate
        except ValueError:
            pass
    return get_data_dir() / "biometria" / f"empleado_{employee_id}"


def save_employee_images(employee_id: int, uploads, stored_path: str | None = None) -> tuple[Path, int]:
    uploads = list(uploads or [])
    existing_files = list_employee_images(employee_id, stored_path)
    if len(existing_files) + len(uploads) > MAX_IMAGES_PER_EMPLOYEE:
        raise ValueError(f"Se permiten hasta {MAX_IMAGES_PER_EMPLOYEE} imágenes por empleado.")
    try:
        total_bytes = sum(len(upload.getvalue() or b"") for upload in uploads)
    except Exception:
        raise ValueError("No se pudieron leer las imágenes seleccionadas.") from None
    if total_bytes > MAX_BATCH_IMAGE_BYTES:
        raise ValueError("El lote de imágenes debe pesar 64 MB o menos.")

    prepared: list[tuple[Image.Image, str, str]] = []
    try:
        for upload in uploads:
            raw = upload.getvalue()
            if not raw:
                continue
            if len(raw) > MAX_IMAGE_BYTES:
                raise ValueError("Cada imagen debe pesar 8 MB o menos.")

            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("error", Image.DecompressionBombWarning)
                    with Image.open(io.BytesIO(raw)) as check:
                        check.verify()
                    with Image.open(io.BytesIO(raw)) as image:
                        image_format = (image.format or "").upper()
                        if image_format not in ALLOWED_FORMATS:
                            raise ValueError("Solo se aceptan imágenes JPG o PNG válidas.")
                        if image.width * image.height > MAX_IMAGE_PIXELS:
                            raise ValueError("Cada imagen debe tener 40 megapíxeles o menos.")
                        image = ImageOps.exif_transpose(image)
                        if image_format == "JPEG":
                            image = image.convert("RGB")
                        prepared.append(
                            (image.copy(), image_format, f"rostro_{uuid.uuid4().hex}{ALLOWED_FORMATS[image_format]}")
                        )
            except (OSError, Image.DecompressionBombError, Image.DecompressionBombWarning):
                raise ValueError("Una de las imágenes no se pudo procesar. Volvé a exportarla como JPG o PNG.") from None
    except ValueError:
        for image, _, _ in prepared:
            image.close()
        raise
    except Exception:
        for image, _, _ in prepared:
            image.close()
        raise ValueError("No se pudieron validar las imágenes seleccionadas.") from None

    folder = employee_photo_dir(employee_id)
    try:
        folder.mkdir(parents=True, exist_ok=True)
    except OSError:
        raise ValueError("No se pudo crear la carpeta biométrica local.") from None
    legacy_folder = employee_photo_dir(employee_id, stored_path)
    if legacy_folder.resolve() != folder.resolve() and legacy_folder.is_dir():
        try:
            for old_image in existing_files:
                destination = folder / old_image.name
                if not destination.exists():
                    shutil.copy2(old_image, destination)
        except OSError:
            raise ValueError("No se pudieron conservar las imágenes biométricas existentes.") from None
    created: list[Path] = []
    try:
        for image, image_format, filename in prepared:
            destination = folder / filename
            if image_format == "JPEG":
                image.save(destination, format="JPEG", quality=92, optimize=True)
            else:
                image.save(destination, format="PNG", optimize=True)
            created.append(destination)
    except (OSError, ValueError):
        for path in created:
            path.unlink(missing_ok=True)
        raise ValueError("No se pudieron guardar las imágenes en el almacenamiento local.") from None
    finally:
        for image, _, _ in prepared:
            image.close()

    return folder, len(created)


def list_employee_images(employee_id: int, stored_path: str | None = None) -> list[Path]:
    folder = employee_photo_dir(employee_id, stored_path)
    if not folder.is_dir():
        return []
    try:
        base = folder.resolve()
        files = [
            path for path in folder.iterdir()
            if path.is_file()
            and path.suffix.lower() in {".jpg", ".jpeg", ".png"}
            and path.resolve().parent == base
        ]
        return sorted(files, key=lambda path: path.name.casefold())
    except OSError:
        return []


def delete_employee_image(employee_id: int, filename: str, stored_path: str | None = None) -> None:
    safe_name = Path(str(filename)).name
    if safe_name != filename or Path(safe_name).suffix.lower() not in {".jpg", ".jpeg", ".png"}:
        raise ValueError("Nombre de archivo no válido.")
    folder = employee_photo_dir(employee_id, stored_path).resolve()
    target = (folder / safe_name).resolve()
    if target.parent != folder:
        raise ValueError("La ruta de la imagen no es válida.")
    target.unlink(missing_ok=True)


def media_directory() -> Path:
    explicit = os.getenv("MEDIA_DIR")
    if explicit:
        return Path(explicit).expanduser().resolve()
    app_dir = get_app_dir()
    legacy = app_dir / "data" / "highlights_media_bd"
    if legacy.is_dir():
        return legacy.resolve()
    return get_data_dir() / "videos"


def safe_video_path(database_path: str | None) -> Path | None:
    if not database_path:
        return None
    filename = Path(str(database_path).replace("\\", "/")).name
    if not filename or filename in {".", ".."}:
        return None
    base = media_directory().resolve()
    candidate = (base / filename).resolve()
    try:
        candidate.relative_to(base)
    except ValueError:
        return None
    return candidate if candidate.is_file() else None


def detect_video_duration(path: str | Path) -> int:
    """Lee la duración real con el FFmpeg distribuido junto a la aplicación."""
    try:
        import imageio_ffmpeg

        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0
        result = subprocess.run(
            [imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-i", str(path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            creationflags=flags,
            check=False,
        )
    except (OSError, subprocess.SubprocessError, ImportError, RuntimeError):
        raise ValueError("No se pudo detectar la duración del video. Probá exportarlo nuevamente como MP4, WebM o MOV.") from None
    match = re.search(r"Duration:\s*(\d{1,4}):(\d{2}):(\d{2})(?:\.(\d+))?", result.stderr or "")
    if not match:
        raise ValueError("El video no informa una duración válida o está dañado.")
    hours, minutes, seconds = (int(match.group(index)) for index in (1, 2, 3))
    duration = hours * 3600 + minutes * 60 + seconds
    if duration < 1:
        raise ValueError("El video debe durar al menos un segundo para poder seleccionar un tramo.")
    return duration


def format_video_duration(seconds: int) -> str:
    seconds = int(seconds)
    return f"{seconds // 3600:02d}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d}"


def save_video_upload(upload) -> tuple[str, int, int]:
    """Guarda un clip validado bajo nombre generado, confinado a la carpeta local."""
    original_name = Path(str(getattr(upload, "name", ""))).name
    suffix = Path(original_name).suffix.lower()
    if suffix not in ALLOWED_VIDEO_SUFFIXES:
        raise ValueError("Solo se aceptan videos MP4, WebM o MOV.")
    try:
        raw = upload.getvalue()
    except Exception:
        raise ValueError("No se pudo leer el archivo seleccionado.") from None
    if not raw:
        raise ValueError("El archivo está vacío.")
    if len(raw) > MAX_VIDEO_BYTES:
        raise ValueError("El video supera el límite de 200 MB.")
    if suffix in {".mp4", ".mov"} and (len(raw) < 12 or raw[4:8] != b"ftyp"):
        raise ValueError("El contenido no parece ser un video MP4/MOV válido.")
    if suffix == ".webm" and not raw.startswith(b"\x1a\x45\xdf\xa3"):
        raise ValueError("El contenido no parece ser un video WebM válido.")
    folder = media_directory().resolve()
    target = None
    try:
        folder.mkdir(parents=True, exist_ok=True)
        filename = f"clip_{uuid.uuid4().hex}{suffix}"
        target = (folder / filename).resolve()
        target.relative_to(folder)
        with target.open("xb") as output:
            output.write(raw)
        duration = detect_video_duration(target)
    except (OSError, ValueError) as exc:
        if target is not None:
            try:
                target.unlink(missing_ok=True)
            except OSError:
                pass
        if isinstance(exc, ValueError):
            raise
        raise ValueError("No se pudo guardar el video en el almacenamiento local.") from None
    return filename, len(raw), duration


def media_url(filename: str) -> str:
    base_url = os.getenv("ARGOS_MEDIA_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    return f"{base_url}/static/videos/{quote(Path(filename).name)}"
