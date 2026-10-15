from __future__ import annotations

import asyncio
import html
import logging
import sys
import time
from datetime import date, datetime, time as dtime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend import SPs as api
from backend import storage
from frontend.panels import render_performance, render_security

logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="ArgosIA",
    layout="wide",
    page_icon="🔒",
    initial_sidebar_state="collapsed",
)

try:
    css = Path(__file__).with_name("styles.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
except OSError:
    st.warning("No se pudo cargar el estilo visual. La app seguirá disponible.")


def _database_message(exc: Exception) -> str:
    if isinstance(exc, api.DatabaseConfigurationError):
        return str(exc)
    if isinstance(exc, api.DatabaseSchemaError):
        return str(exc)
    if isinstance(exc, api.DatabaseUnavailableError):
        return "Turso no está disponible. Revisá la conexión a internet y la configuración local; la app no guardó cambios."
    return "No se pudo completar la operación en Turso. Revisá la conexión y los datos relacionados."


def db_call(coro, fallback=None):
    operation = getattr(getattr(coro, "cr_code", None), "co_name", "")
    audit_operations = {
        "crear_rol": ("Alta de puesto", "rol_empleado", None),
        "eliminar_rol": ("Baja de puesto", "rol_empleado", "rol_id"),
        "crear_empleado": ("Alta de empleado", "empleado", None),
        "actualizar_empleado": ("Modificación de empleado", "empleado", "empleado_id"),
        "reintegrar_empleado": ("Reintegración de empleado", "empleado", "empleado_id"),
        "actualizar_ruta_imagen": ("Actualización de plantilla biométrica", "empleado", "empleado_id"),
        "cargar_dias_semana_si_vacio": ("Carga del catálogo de días", "diasSemana", None),
        "asignar_turno_completo": ("Alta de turno", "turno", None),
        "actualizar_turno_completo": ("Modificación de turno", "turno", "turno_id"),
        "eliminar_turno": ("Baja de turno", "turno", "turno_id"),
        "registrar_jornada_manual": ("Carga manual de jornada", "horas", None),
        "registrar_video": ("Carga de clip", "video", None),
        "registrar_highlight": ("Alta de highlight", "highlights", None),
        "registrar_evento_seguridad": ("Alta de evento de seguridad", "mov_sospechoso", None),
        "guardar_alerta": ("Alta manual de alerta", "alerta", None),
        "registrar_revision_alerta": ("Revisión de alerta", "revision_alerta", None),
    }

    async def run_action():
        frame = getattr(coro, "cr_frame", None)
        parameters = frame.f_locals.copy() if frame else {}
        result = await coro
        if operation in audit_operations and result is not None and result is not False:
            user_id = st.session_state.get("user_id")
            if user_id:
                label, table, id_parameter = audit_operations[operation]
                record_id = result if isinstance(result, int) and not isinstance(result, bool) else parameters.get(id_parameter) if id_parameter else None
                try:
                    await api.registrar_auditoria_accion(user_id, label, table, record_id)
                except Exception as audit_error:
                    logger.warning("No se pudo registrar el actor de una acción (%s).", type(audit_error).__name__)
                    st.warning("El cambio se guardó, pero no se pudo completar su registro de auditoría. Revisá la conexión con Turso.")
        return result

    try:
        result = asyncio.run(run_action())
        st.session_state["_argos_db_error"] = False
        return result
    except ValueError as exc:
        st.warning(str(exc))
        st.session_state["_argos_db_error"] = False
    except (api.DatabaseConfigurationError, api.DatabaseUnavailableError, api.DatabaseSchemaError, api.DatabaseOperationError) as exc:
        logger.warning("Operación de la interfaz cancelada (%s).", type(exc).__name__)
        st.session_state["_argos_db_error"] = True
        st.error(_database_message(exc))
    except Exception as exc:
        logger.warning("Fallo inesperado en la interfaz (%s).", type(exc).__name__)
        st.session_state["_argos_db_error"] = True
        st.error("Ocurrió un problema inesperado. No se guardaron los cambios; volvé a intentar.")
    return fallback


def flash(message: str, kind: str = "success") -> None:
    st.session_state["_argos_flash"] = (kind, message)


def render_flash() -> None:
    item = st.session_state.pop("_argos_flash", None)
    if not item:
        return
    kind, message = item
    getattr(st, kind, st.info)(message)


def badge(text: str, kind: str = "info") -> str:
    safe_kind = kind if kind in {"danger", "warning", "success", "info"} else "info"
    return f'<span class="badge badge-{safe_kind}">{html.escape(str(text))}</span>'


def module_header(icon: str, title: str, subtitle: str = "") -> None:
    st.markdown(
        f"""<div class="module-header"><h2>{html.escape(icon)} {html.escape(title)}</h2>
        {f'<p>{html.escape(subtitle)}</p>' if subtitle else ''}</div>""",
        unsafe_allow_html=True,
    )


def kpi(value, label: str) -> str:
    return (
        f'<div class="kpi-box"><div class="kpi-value">{html.escape(str(value))}</div>'
        f'<div class="kpi-label">{html.escape(label)}</div></div>'
    )


def _login(database_ready: bool = True) -> None:
    col = st.columns([1, 1.2, 1])[1]
    with col:
        st.markdown(
            """<div class="login-card"><div class="login-logo">🔒</div>
            <div class="login-title">ArgosIA</div>
            <div class="login-sub">Sistema de Monitoreo Inteligente<br>Identificación obligatoria de operador</div></div>""",
            unsafe_allow_html=True,
        )
        lock_until = float(st.session_state.get("_argos_lock_until", 0))
        locked_for = max(0, int(lock_until - time.monotonic()))
        if locked_for:
            st.error(f"Demasiados intentos. Volvé a intentar en {locked_for} segundos.")
        with st.form("argos_login_form"):
            email = st.text_input("Correo Electrónico", placeholder="tu correo registrado", key="login_email")
            password = st.text_input("Contraseña", type="password", placeholder="••••••••", key="login_password")
            submitted = st.form_submit_button(
                "Iniciar Sesión", use_container_width=True, type="primary",
                disabled=locked_for > 0 or not database_ready,
            )
        if st.session_state.pop("_argos_bad_credentials", False):
            st.error("Correo electrónico o contraseña incorrectos.")
        if submitted:
            if not email.strip() or not password:
                st.warning("Completá el correo y la contraseña.")
            else:
                user = db_call(api.autenticar_usuario(email, password))
                if user:
                    st.session_state.autenticado = True
                    st.session_state.user_id = user["id"]
                    st.session_state.user_nombre = user["nombre"]
                    st.session_state.last_login = datetime.now().strftime("%d/%m/%Y %H:%M")
                    st.session_state.menu_actual = "📺 Monitoreo"
                    st.session_state["_argos_login_attempts"] = 0
                    st.session_state["_argos_lock_until"] = 0
                    flash("Sesión iniciada.")
                    st.rerun()
                elif not st.session_state.get("_argos_db_error"):
                    attempts = int(st.session_state.get("_argos_login_attempts", 0)) + 1
                    if attempts >= 5:
                        st.session_state["_argos_login_attempts"] = 0
                        st.session_state["_argos_lock_until"] = time.monotonic() + 60
                    else:
                        st.session_state["_argos_login_attempts"] = attempts
                        st.session_state["_argos_bad_credentials"] = True
                    st.rerun()
        st.caption("El registro de nuevos operadores está deshabilitado. Las cuentas se administran fuera de esta app.")


if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "menu_actual" not in st.session_state:
    st.session_state.menu_actual = "📺 Monitoreo"
if "user_nombre" not in st.session_state:
    st.session_state.user_nombre = "Operador"
if "user_id" not in st.session_state:
    st.session_state.user_id = None

render_flash()
if not st.session_state.get("_argos_schema_ok", False):
    database_ready = db_call(api.verificar_esquema_y_conexion()) is True
    if database_ready:
        st.session_state["_argos_schema_ok"] = True
else:
    database_ready = db_call(api.verificar_conexion()) is True
if not database_ready:
    if not st.session_state.autenticado:
        _login(database_ready=False)
    st.stop()

if not st.session_state.autenticado:
    _login()
    st.stop()

MENU_ITEMS = [
    ("📺", "Monitoreo"),
    ("👥", "Empleados"),
    ("📈", "Rendimiento"),
    ("🛡️", "Seguridad"),
    ("👤", "Mi Perfil"),
]
DEMO_LIVE_SOURCES = {
    "🌴 Venice Beach — California": "https://www.youtube.com/watch?v=98jOtUeM3m8",
    "🏖️ Playa Camp de Mar — Mallorca": "https://www.youtube.com/watch?v=ycQWM6fNm_4",
    "🗼 Montmartre — París": "https://www.youtube.com/watch?v=gGIBi-Uxal0",
    "🚦 Shibuya Crossing — Tokio": "https://www.youtube.com/watch?v=3Q5wZeTuttw",
}
menu = st.session_state.menu_actual

if menu == "📺 Monitoreo":
    module_header(
        "📺", "Monitoreo Analítico",
        "Procesamiento de video e identificación de actividades en el entorno comercial.",
    )
    tab_live, tab_recordings, tab_upload = st.tabs(["▶ Actividad en tiempo real", "🗄 Ver grabaciones", "⬆ Cargar clip"])
    cameras = db_call(api.obtener_camaras(), []) or []
    camera_labels = {f"{row['ubicacion'] or 'Cámara'} (ID {row['id']})": row for row in cameras}

    with tab_live:
        st.markdown("#### Fuentes públicas de demostración")
        demo_label = st.selectbox("Seleccioná una cámara demo en vivo", list(DEMO_LIVE_SOURCES), key="demo_live_source")
        st.video(DEMO_LIVE_SOURCES[demo_label])
        st.caption("Son transmisiones públicas de terceros para probar la reproducción; pueden pausarse o cambiar sin aviso. No se guardan ni se presentan como cámaras de la heladería.")
        st.markdown("---")
        if not cameras:
            st.info("No hay cámaras propias registradas en Turso. Las fuentes demo de arriba funcionan sin modificar la base.")
        else:
            col_select, col_status = st.columns([2, 1])
            selected_camera_label = col_select.selectbox("Cámara activa", list(camera_labels), key="live_camera")
            selected_camera = camera_labels[selected_camera_label]
            camera_status = str(selected_camera.get("estado") or "Sin estado")
            with col_status:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown(badge(camera_status.upper(), "success" if camera_status.casefold() in {"activa", "activo", "conectada", "online"} else "warning"), unsafe_allow_html=True)
            location = html.escape(str(selected_camera.get("ubicacion") or "Cámara sin ubicación"))
            st.markdown(
                f'<div class="argos-card"><h3>{location}</h3><p>Vista de monitoreo</p>'
                '<p style="color:var(--text-muted);">La base guarda el estado y la IP de la cámara, pero no define un endpoint de video reproducible.</p></div>',
                unsafe_allow_html=True,
            )
            st.markdown("---")
            st.markdown("**Miniaturas — Resto de cámaras**")
            other_cameras = [row for row in cameras if row["id"] != selected_camera["id"]]
            if other_cameras:
                thumbnails = st.columns(min(3, len(other_cameras)))
                for index, row in enumerate(other_cameras):
                    name = html.escape(str(row.get("ubicacion") or f"Cámara {row['id']}"))
                    state = html.escape(str(row.get("estado") or "Sin estado"))
                    with thumbnails[index % len(thumbnails)]:
                        st.markdown(
                            f'<div class="argos-card"><b>{name}</b><br><span style="color:var(--text-muted);">{state}</span></div>',
                            unsafe_allow_html=True,
                        )
            else:
                st.info("No hay otras cámaras registradas.")

    with tab_recordings:
        if not cameras:
            st.info("No hay cámaras registradas para buscar grabaciones.")
        else:
            col_date, col_camera, col_slot = st.columns([1.2, 1.2, 1])
            recording_date = col_date.date_input("Fecha", value=date.today(), key="recording_date")
            recording_camera_label = col_camera.selectbox("Cámara", list(camera_labels), key="recording_camera")
            time_slot = col_slot.selectbox(
                "Franja horaria", ["00:00–06:00", "06:00–12:00", "12:00–18:00", "18:00–24:00"], key="recording_slot"
            )
            if st.button("🔍 Buscar grabación", type="primary", key="search_recording"):
                camera_id = camera_labels[recording_camera_label]["id"]
                recordings = db_call(api.buscar_grabaciones(recording_date.isoformat(), camera_id, time_slot), []) or []
                if not recordings:
                    st.info("No se encontraron grabaciones para esos filtros.")
                else:
                    if any(not row["franja_aplicable"] for row in recordings):
                        st.caption("La columna fecha no contiene hora en todos los registros; para esos videos se muestran todas las grabaciones del día.")
                    for recording in recordings:
                        title = f"🎞 Grabación {recording.get('fecha') or ''} · ID {recording['id']}"
                        with st.expander(title):
                            if recording.get("url_reproduccion"):
                                st.video(recording["url_reproduccion"])
                            else:
                                st.warning("El registro está en Turso, pero el archivo no está en esta computadora.")
                            st.caption(f"Duración: {recording.get('duracion') or '—'} · Franja: {recording.get('tiempo_limite') or time_slot}")

    with tab_upload:
        st.markdown("#### Guardar un clip de prueba")
        st.caption("El archivo se guarda localmente en ArgosIA/videos. Turso recibe solo la ruta y los metadatos. El esquema permite asociar una cámara existente o dejarla vacía para una prueba.")
        upload_camera_options = {"Sin cámara asociada": None, **{label: row["id"] for label, row in camera_labels.items()}}
        with st.form("upload_video_form"):
            upload_camera = st.selectbox("Cámara asociada (opcional)", list(upload_camera_options), key="upload_video_camera")
            video_file = st.file_uploader("Video MP4, WebM o MOV (máximo 200 MB)", type=["mp4", "webm", "mov"], key="upload_video_file")
            video_date = st.date_input("Fecha del clip", value=date.today(), key="upload_video_date")
            video_time = st.time_input("Hora", value=datetime.now().time().replace(second=0, microsecond=0), key="upload_video_time")
            submit_video = st.form_submit_button("⬆ Guardar clip y registrar en Turso", type="primary")
        if submit_video:
            if video_file is None:
                st.warning("Elegí un archivo de video antes de guardar.")
            else:
                try:
                    filename, byte_count, duration_seconds = storage.save_video_upload(video_file)
                except ValueError as exc:
                    st.error(str(exc))
                else:
                    video_id = db_call(api.registrar_video(
                        filename, datetime.combine(video_date, video_time).strftime("%Y-%m-%d %H:%M:%S"),
                        byte_count, upload_camera_options[upload_camera],
                    ))
                    if video_id is not None:
                        flash(f"Clip de {storage.format_video_duration(duration_seconds)} guardado y registrado en Turso con ID {video_id}.")
                        st.rerun()
                    else:
                        st.warning(f"El archivo quedó guardado en esta computadora como {filename}, pero Turso no pudo registrar sus metadatos. No se perdió el clip.")


elif menu == "👥 Empleados":
    module_header("👥", "Gestión de Empleados", "Puestos, datos del personal, turnos y plantilla biométrica.")
    tab_roles, tab_create, tab_shifts, tab_edit, tab_list = st.tabs(
        [
            "🧩 Puestos", "➕ Alta de empleado", "🕐 Registrar turno",
            "✏️ Modificar empleado", "🗑 Empleados dados de baja",
        ]
    )

    roles = db_call(api.obtener_roles(), []) or []
    employees = db_call(api.obtener_empleados(), []) or []
    role_by_name = {f"{row['nombre']} (ID {row['id']})": row for row in roles}
    employee_by_label = {f"{row['nombre']} (ID {row['id']})": row for row in employees}

    with tab_roles:
        st.markdown("#### Puestos existentes")
        if roles:
            st.dataframe(
                pd.DataFrame(roles).rename(columns={"id": "ID", "nombre": "Puesto", "descripcion": "Descripción"}),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No hay puestos cargados. Agregá uno antes de registrar empleados.")
        st.markdown("---")
        st.subheader("➕ Cargar nuevo puesto")
        with st.form("create_role_form"):
            c1, c2 = st.columns(2)
            role_name = c1.text_input("Nombre del puesto", key="role_name_new")
            role_description = c2.text_input("Descripción", key="role_description_new")
            save_role = st.form_submit_button("💾 Guardar puesto", type="primary")
        if save_role:
            role_id = db_call(api.crear_rol(role_name, role_description))
            if role_id is not None:
                flash("Puesto guardado correctamente.")
                st.rerun()
        if roles:
            st.markdown("#### Eliminar puesto")
            removable = st.selectbox(
                "Puesto a borrar", list(role_by_name), key="delete_role_choice"
            )
            role_in_use = any(int(row.get("rol_id") or 0) == int(role_by_name[removable]["id"]) for row in employees)
            if role_in_use:
                st.caption("Este puesto tiene empleados asociados y no se puede borrar hasta reasignarlos.")
            if st.button("🗑 Borrar puesto", key="delete_role", disabled=role_in_use):
                if db_call(api.eliminar_rol(role_by_name[removable]["id"]), fallback=False) is True:
                    flash("Puesto eliminado.")
                    st.rerun()

    with tab_create:
        if not roles:
            st.info("Cargá primero un puesto en la pestaña Puestos.")
        else:
            with st.form("create_employee_form"):
                left, right = st.columns(2)
                with left:
                    st.subheader("Datos personales y laborales")
                    name = st.text_input("Nombre completo", key="new_employee_name")
                    gender = st.selectbox("Género", ["Masculino", "Femenino", "Otro"], key="new_employee_gender")
                    status = st.selectbox("Estado", ["Activo", "Inactivo"], key="new_employee_status")
                    performance = st.number_input(
                        "Rendimiento (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.5, key="new_employee_performance"
                    )
                    role_label = st.selectbox("Puesto asignado", list(role_by_name), key="new_employee_role")
                with right:
                    st.subheader("Perfil biométrico multi-imagen")
                    st.caption("Podés adjuntar varias fotos JPG o PNG. Se guardan en esta computadora.")
                    photos = st.file_uploader(
                        "Imágenes de referencia facial", type=["jpg", "jpeg", "png"], accept_multiple_files=True,
                        key="new_employee_photos",
                    )
                    if photos:
                        previews = st.columns(min(len(photos), 4))
                        for index, photo in enumerate(photos):
                            previews[index % len(previews)].image(photo.getvalue(), use_container_width=True)
                save_employee = st.form_submit_button("💾 Guardar empleado", type="primary")
            if save_employee:
                role_id = role_by_name[role_label]["id"]
                employee_id = db_call(api.crear_empleado(name, gender, performance, role_id, status))
                if employee_id is not None:
                    saved_count = 0
                    image_warning = ""
                    if photos:
                        try:
                            _, saved_count = storage.save_employee_images(employee_id, photos)
                            if saved_count:
                                path_saved = db_call(
                                    api.actualizar_ruta_imagen(employee_id, storage.relative_employee_path(employee_id))
                                )
                                if path_saved is not True:
                                    image_warning = " Las fotos quedaron en esta computadora, pero no se pudo actualizar la referencia en Turso."
                        except ValueError as exc:
                            image_warning = f" Las imágenes no se guardaron: {exc}"
                    flash(
                        f"Empleado registrado con ID {employee_id}. Imágenes guardadas: {saved_count}.{image_warning}",
                        "warning" if image_warning else "success",
                    )
                    st.rerun()

    with tab_shifts:
        active_employees = [row for row in employees if str(row.get("estado", "")).casefold() == "activo"]
        days = db_call(api.obtener_dias_semana(), []) or []
        shifts = db_call(api.obtener_turnos(), []) or []
        if not active_employees:
            st.info("No hay empleados activos para asignar turnos.")
        elif not days:
            st.warning("La tabla diasSemana está vacía. No se modificó el esquema.")
            if st.button("Cargar catálogo estándar de días", key="load_weekday_catalog"):
                created = db_call(api.cargar_dias_semana_si_vacio(), fallback=False)
                if created is True:
                    flash("Se cargaron los siete días en el catálogo existente.")
                    st.rerun()
                elif created is False:
                    st.info("El catálogo ya no está vacío. Actualizá la pantalla.")
        else:
            employee_labels = {f"{row['nombre']} (ID {row['id']})": row for row in active_employees}
            day_names = {str(row["dia"]): int(row["id"]) for row in days}
            with st.form("register_shift_form"):
                shift_employee = st.selectbox("Seleccioná el empleado", list(employee_labels), key="shift_employee")
                selected_days = st.multiselect("Días de la semana", list(day_names), key="shift_days")
                c1, c2 = st.columns(2)
                start_time = c1.time_input("Hora de entrada", value=dtime(8, 0), key="shift_start")
                end_time = c2.time_input("Hora de salida", value=dtime(16, 0), key="shift_end")
                worked_hours = ((datetime.combine(date.today(), end_time) + timedelta(days=1)) - datetime.combine(date.today(), start_time)).total_seconds() / 3600 if end_time <= start_time else (datetime.combine(date.today(), end_time) - datetime.combine(date.today(), start_time)).total_seconds() / 3600
                st.info(f"⏱ Duración: **{worked_hours:.1f} hs**. El DDL guarda días recurrentes y no contempla descanso.")
                save_shift = st.form_submit_button("📋 Registrar turno", type="primary")
            if save_shift:
                selected_ids = [day_names[name] for name in selected_days]
                shift_id = db_call(
                    api.asignar_turno_completo(
                        employee_labels[shift_employee]["id"], start_time.strftime("%H:%M:%S"),
                        end_time.strftime("%H:%M:%S"), selected_ids,
                    )
                )
                if shift_id is not None:
                    flash(f"Turno registrado con ID {shift_id}.")
                    st.rerun()

        st.markdown("#### Turnos registrados")
        if shifts:
            st.dataframe(
                pd.DataFrame(shifts).rename(
                    columns={
                        "id": "ID", "empleado_id": "ID empleado", "empleado": "Empleado", "dias": "Días",
                        "hora_inicio": "Entrada", "hora_fin": "Salida",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )
            st.markdown("#### Modificar turno")
            shift_map = {f"#{row['id']} · {row.get('empleado') or 'Empleado'} · {row.get('dias') or 'Sin días'}": row for row in shifts}
            with st.form("edit_shift_form"):
                selected_shift_label = st.selectbox("Turno a modificar", list(shift_map), key="edit_shift_choice")
                selected_shift = shift_map[selected_shift_label]
                current_employee_label = next(
                    (label for label, row in employee_by_label.items() if int(row["id"]) == int(selected_shift.get("empleado_id") or 0)),
                    next(iter(employee_by_label)),
                )
                edit_employee = st.selectbox("Empleado", list(employee_by_label), index=list(employee_by_label).index(current_employee_label), key=f"edit_shift_employee_{selected_shift['id']}")
                current_days = [part.strip() for part in str(selected_shift.get("dias") or "").split(",") if part.strip() in day_names]
                edit_days = st.multiselect("Días de la semana", list(day_names), default=current_days, key=f"edit_shift_days_{selected_shift['id']}")
                try:
                    edit_start_default = dtime.fromisoformat(str(selected_shift.get("hora_inicio") or "08:00")[:8])
                except ValueError:
                    edit_start_default = dtime(8, 0)
                try:
                    edit_end_default = dtime.fromisoformat(str(selected_shift.get("hora_fin") or "16:00")[:8])
                except ValueError:
                    edit_end_default = dtime(16, 0)
                e1, e2 = st.columns(2)
                edit_start = e1.time_input("Entrada", value=edit_start_default, key=f"edit_shift_start_{selected_shift['id']}")
                edit_end = e2.time_input("Salida", value=edit_end_default, key=f"edit_shift_end_{selected_shift['id']}")
                update_shift = st.form_submit_button("💾 Guardar cambios del turno", type="primary")
            if update_shift:
                update_result = db_call(api.actualizar_turno_completo(
                    selected_shift["id"], employee_by_label[edit_employee]["id"],
                    edit_start.strftime("%H:%M:%S"), edit_end.strftime("%H:%M:%S"),
                    [day_names[value] for value in edit_days],
                ), fallback=False)
                if update_result is True:
                    flash("Turno actualizado.")
                    st.rerun()
            with st.form("delete_shift_form"):
                delete_shift_label = st.selectbox("Turno a borrar", list(shift_map), key="delete_shift_choice")
                confirm_shift_delete = st.checkbox("Confirmo borrar este turno.", key="confirm_delete_shift")
                delete_shift_submit = st.form_submit_button("🗑 Borrar turno")
            if delete_shift_submit:
                if not confirm_shift_delete:
                    st.warning("Confirmá el borrado del turno.")
                elif db_call(api.eliminar_turno(shift_map[delete_shift_label]["id"]), fallback=False) is True:
                    flash("Turno eliminado.")
                    st.rerun()
        else:
            st.info("Todavía no hay turnos registrados.")

    with tab_list:
        inactive_employees = [row for row in employees if str(row.get("estado") or "").casefold() == "inactivo"]
        if not inactive_employees:
            st.info("Todavía no hay empleados dados de baja.")
        else:
            display_rows = [
                {"ID": row["id"], "Nombre": row["nombre"], "Género": row["genero"],
                 "Puesto": row["puesto"] or "—", "Rendimiento %": row["rendimiento"]}
                for row in inactive_employees
            ]
            st.markdown("#### Empleados dados de baja")
            st.dataframe(pd.DataFrame(display_rows), use_container_width=True, hide_index=True)
            for inactive_employee in inactive_employees:
                employee_id = int(inactive_employee["id"])
                name = str(inactive_employee.get("nombre") or "Empleado")
                if st.button(f"↩️ Reintegrar {name} (ID {employee_id})", key=f"reinstate_employee_{employee_id}"):
                    if db_call(api.reintegrar_empleado(employee_id), fallback=False) is True:
                        flash(f"{name} fue reintegrado y volvió a figurar como activo.")
                        st.rerun()

        st.markdown("---")
        st.subheader("🗑 Dar de baja empleado")
        active_options = {
            f"{row['nombre']} (ID {row['id']})": row
            for row in employees
            if str(row.get("estado", "")).casefold() == "activo"
        }
        if active_options:
            with st.form("deactivate_employee_form"):
                chosen_employee = st.selectbox("Seleccioná el empleado", list(active_options), key="deactivate_employee")
                reason = st.text_input("Motivo de la baja (requerido)", max_chars=500, key="deactivate_reason")
                confirm = st.checkbox(
                    "Confirmo que quiero dar de baja al empleado conservando sus datos e historial.",
                    key="deactivate_confirm",
                )
                submitted = st.form_submit_button("🗑 Dar de baja", type="primary")
            if submitted:
                if not reason.strip():
                    st.warning("Ingresá el motivo de la baja.")
                elif not confirm:
                    st.warning("Marcá la confirmación para continuar.")
                elif db_call(
                    api.dar_de_baja_empleado(
                        active_options[chosen_employee]["id"], st.session_state.user_id, reason
                    ),
                    fallback=False,
                ) is True:
                    flash("Empleado dado de baja. Se conservaron sus registros relacionados.")
                    st.rerun()
        else:
            st.info("No hay empleados activos para dar de baja.")

    with tab_edit:
        if not employees:
            st.info("No hay empleados registrados en Turso.")
        else:
            labels = list(employee_by_label)
            selected_label = st.selectbox("Seleccioná el empleado a gestionar", labels, key="manage_employee")
            employee = employee_by_label[selected_label]
            employee_id = int(employee["id"])
            role_names = list(role_by_name) or ["(sin puestos configurados)"]
            role_index = (
                next((i for i, label in enumerate(role_names) if role_by_name[label]["id"] == employee["rol_id"]), 0)
                if role_by_name else 0
            )

            st.markdown(f"**Legajo ID: {employee_id}**")
            c1, c2 = st.columns(2)
            with c1:
                new_name = st.text_input("Nombre completo", value=str(employee["nombre"] or ""), key=f"edit_name_{employee_id}")
                genders = ["Masculino", "Femenino", "Otro"]
                current_gender = str(employee.get("genero") or "Otro")
                gender_index = genders.index(current_gender) if current_gender in genders else 2
                new_gender = st.selectbox("Género", genders, index=gender_index, key=f"edit_gender_{employee_id}")
                current_status = str(employee.get("estado") or "Inactivo").capitalize()
                new_status = current_status
                st.caption(f"Estado: {current_status}. Las bajas se gestionan desde la pestaña correspondiente para registrar su motivo.")
                new_performance = st.number_input(
                    "Rendimiento (%)", min_value=0.0, max_value=100.0,
                    value=min(100.0, max(0.0, float(employee.get("rendimiento") or 0))), step=0.5,
                    key=f"edit_performance_{employee_id}",
                )
            new_role = st.selectbox("Puesto", role_names, index=role_index, key=f"edit_role_{employee_id}")
            if not role_by_name:
                st.warning("No se puede modificar el puesto hasta que vuelva a existir un registro en rol_empleado.")
            with c2:
                st.markdown("⚙️ **Plantilla biométrica local**")
                image_files = storage.list_employee_images(employee_id, employee.get("urlImagen"))
                if image_files:
                    st.caption(f"Se guardaron {len(image_files)} imágenes en esta computadora.")
                    image_columns = st.columns(min(len(image_files), 4))
                    for index, image_path in enumerate(image_files):
                        with image_columns[index % len(image_columns)]:
                            st.image(str(image_path), caption=image_path.name, use_container_width=True)
                            if st.button("🗑 Borrar", key=f"delete_image_{employee_id}_{index}"):
                                try:
                                    storage.delete_employee_image(employee_id, image_path.name, employee.get("urlImagen"))
                                    db_call(api.registrar_auditoria_accion(
                                        st.session_state.user_id, "Eliminación local de imagen biométrica",
                                        "empleado", employee_id,
                                    ), fallback=False)
                                    flash("Imagen eliminada de esta computadora.")
                                    st.rerun()
                                except (OSError, ValueError):
                                    st.error("No se pudo eliminar esa imagen local.")
                else:
                    st.info("Este perfil todavía no tiene imágenes locales.")
                more_photos = st.file_uploader(
                    "Adjuntar más imágenes", type=["jpg", "jpeg", "png"], accept_multiple_files=True,
                    key=f"add_images_{employee_id}",
                )

            if st.button("💾 Guardar cambios", type="primary", key=f"save_employee_{employee_id}"):
                if not role_by_name:
                    st.warning("No se guardaron cambios porque la tabla de puestos está vacía.")
                    updated = False
                else:
                    updated = db_call(
                        api.actualizar_empleado(
                            employee_id, new_name, new_gender, new_performance, new_status,
                            role_by_name[new_role]["id"],
                        ),
                        fallback=False,
                    )
                if updated is True:
                    image_warning = ""
                    if more_photos:
                        try:
                            _, count = storage.save_employee_images(employee_id, more_photos, employee.get("urlImagen"))
                            if count:
                                path_saved = db_call(
                                    api.actualizar_ruta_imagen(employee_id, storage.relative_employee_path(employee_id))
                                )
                                if path_saved is not True:
                                    image_warning = " Las imágenes se guardaron localmente, pero no se pudo actualizar su referencia en Turso."
                        except ValueError as exc:
                            image_warning = f" No se agregaron las imágenes: {exc}"
                    flash(
                        f"Datos del empleado actualizados.{image_warning}",
                        "warning" if image_warning else "success",
                    )
                    st.rerun()

elif menu == "📈 Rendimiento":
    render_performance(db_call, badge, kpi)


elif menu == "🛡️ Seguridad":
    render_security(db_call, flash)

elif menu == "👤 Mi Perfil":
    module_header("👤", "Mi Perfil", "Información de la sesión activa.")
    _, center, _ = st.columns([1, 1.4, 1])
    with center:
        user_name = str(st.session_state.get("user_nombre", "Operador"))
        safe_name = html.escape(user_name)
        st.markdown(
            f'<div class="profile-card"><div class="profile-avatar">👤</div><h3>{safe_name}</h3>'
            '<p style="color:var(--text-muted);font-size:.82rem;">Sesión activa</p></div>',
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f'<div class="stat-box"><span class="stat-label">Usuario ID</span><span class="stat-value">{int(st.session_state.user_id)}</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-box"><span class="stat-label">Último acceso</span><span class="stat-value">{html.escape(st.session_state.get("last_login", "—"))}</span></div>', unsafe_allow_html=True)
        st.markdown('<div class="stat-box"><span class="stat-label">Módulos</span><span class="stat-value">5</span></div>', unsafe_allow_html=True)
        if st.button("🚪 Cerrar sesión", use_container_width=True, type="primary", key="logout"):
            for key in ("autenticado", "user_id", "user_nombre", "last_login", "login_email", "login_password"):
                st.session_state.pop(key, None)
            st.session_state.autenticado = False
            st.session_state.user_id = None
            st.session_state.user_nombre = "Operador"
            st.rerun()


# Navegación de pie con widgets nativos: sin HTML onclick ni manipulación del DOM React.
with st.container(key="footer_nav"):
    nav_columns = st.columns(len(MENU_ITEMS))
    for index, (icon, label) in enumerate(MENU_ITEMS):
        full_label = f"{icon} {label}"
        with nav_columns[index]:
            if st.button(
                full_label,
                key=f"nav_{label}",
                use_container_width=True,
                type="primary" if menu == full_label else "secondary",
            ):
                st.session_state.menu_actual = full_label
                st.rerun()
