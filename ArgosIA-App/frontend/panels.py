"""Paneles de rendimiento y seguridad, conectados al esquema existente."""

from __future__ import annotations

import html
import math
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

from backend import SPs as api


def _number(value, default: float = 0.0) -> float:
    try:
        number = float(value)
        return number if math.isfinite(number) else default
    except (TypeError, ValueError, OverflowError):
        return default


def _integer(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return default


def _duration_seconds(value) -> int:
    try:
        hours, minutes, seconds = (int(part) for part in str(value).split(":"))
        return hours * 3600 + minutes * 60 + seconds
    except (TypeError, ValueError):
        return 0


def _bounded_clip_range(prefix: str, duration: int) -> tuple[int, int] | None:
    if duration < 1:
        st.warning("No se conoce la duración del clip. Volvé a cargarlo para detectar sus datos.")
        return None
    st.caption(f"Duración detectada: {duration // 60:02d}:{duration % 60:02d}. Seleccioná un tramo dentro de esos límites.")
    left, right = st.columns(2)
    start = left.number_input(
        "Inicio (segundos)", min_value=0, max_value=duration - 1, value=0, step=1,
        key=f"{prefix}_start_seconds",
    )
    end_key = f"{prefix}_end_seconds"
    min_end = int(start) + 1
    current_end = st.session_state.get(end_key)
    if current_end is not None and int(current_end) < min_end:
        st.session_state[end_key] = min_end
    end = right.number_input(
        "Fin (segundos)", min_value=min_end, max_value=duration,
        value=min(duration, min_end), step=1,
        key=end_key,
    )
    return int(start), int(end)


def _format_clip_time(seconds: int) -> str:
    return f"{seconds // 3600:02d}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d}"


def render_performance(db_call, badge, kpi) -> None:
    st.markdown(
        '<div class="module-header"><h2>📈 Rendimiento Laboral</h2>'
        "<p>Métricas de productividad, validación de jornadas y reproducción de highlights.</p></div>",
        unsafe_allow_html=True,
    )
    tab_metrics, tab_hours, tab_highlights = st.tabs([
        "📊 Métricas de actividad", "✔ Validar jornada laboral", "🎬 Highlights",
    ])

    with tab_metrics:
        period = st.selectbox("Período", ["Hoy", "Última semana", "Último mes"], key="performance_period")
        today = date.today()
        start_date = today - timedelta(days={"Hoy": 0, "Última semana": 6, "Último mes": 29}[period])
        summary = db_call(api.obtener_resumen_rendimiento(start_date.isoformat(), today.isoformat()), {}) or {}
        st.markdown(
            '<div class="kpi-grid">'
            + kpi(summary.get("activos", 0), "Empleados activos")
            + kpi(f"{summary.get('eficiencia', 0)}%", "Eficiencia promedio")
            + kpi(f"{_number(summary.get('horas')):.1f} hs", "Horas registradas")
            + kpi(summary.get("alertas", 0), "Alertas registradas")
            + "</div>",
            unsafe_allow_html=True,
        )
        rows = summary.get("filas", [])
        if rows:
            table = [
                {
                    "Empleado": row.get("nombre") or "—",
                    "Rol": row.get("rol") or "—",
                    "Tareas completadas": _integer(row.get("tareas")),
                    "Eficiencia %": f"{_number(row.get('rendimiento')):.1f}",
                    "Tiempo activo": f"{_number(row.get('horas')):.1f} hs",
                    "Alertas": _integer(row.get("alertas")),
                }
                for row in rows
            ]
            st.dataframe(pd.DataFrame(table), use_container_width=True, hide_index=True)
        else:
            st.info("No hay métricas de empleados para mostrar en este período.")

    with tab_hours:
        employees = db_call(api.obtener_empleados(), []) or []
        if not employees:
            st.info("No hay empleados activos para validar.")
        else:
            by_label = {f"{row['nombre']} (ID {row['id']})": row for row in employees}
            with st.form("query_workday_form"):
                col_employee, col_date = st.columns(2)
                chosen = col_employee.selectbox("Empleado", list(by_label), key="hours_employee")
                selected_date = col_date.date_input("Fecha a consultar", value=date.today(), key="hours_date")
                query_day = st.form_submit_button("🔍 Consultar jornada", type="primary")
            if query_day:
                st.session_state["_workday_query"] = (int(by_label[chosen]["id"]), selected_date.isoformat())
            query = st.session_state.get("_workday_query")
            if query and query[0] in {int(row["id"]) for row in employees}:
                employee = next(row for row in employees if int(row["id"]) == query[0])
                target_date = date.fromisoformat(query[1])
                records = db_call(api.obtener_jornadas_empleado(employee["id"], query[1]), []) or []
                shifts = db_call(api.obtener_turnos(), []) or []
                weekday = ("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo")[target_date.weekday()]
                planned = [row for row in shifts if int(row.get("empleado_id") or 0) == int(employee["id"])
                           and weekday.casefold() in {part.strip().casefold() for part in str(row.get("dias") or "").split(",")}]
                planned_hours = 0.0
                for shift in planned:
                    try:
                        try:
                            shift_start = datetime.strptime(str(shift["hora_inicio"]), "%H:%M:%S")
                        except ValueError:
                            shift_start = datetime.strptime(str(shift["hora_inicio"]), "%H:%M")
                        try:
                            shift_end = datetime.strptime(str(shift["hora_fin"]), "%H:%M:%S")
                        except ValueError:
                            shift_end = datetime.strptime(str(shift["hora_fin"]), "%H:%M")
                        duration = (shift_end - shift_start).total_seconds() / 3600
                        planned_hours += duration if duration > 0 else duration + 24
                    except (KeyError, TypeError, ValueError):
                        continue
                worked_total = 0.0
                in_progress = 0
                for record in records:
                    try:
                        if not record.get("entrada") or not record.get("salida"):
                            in_progress += 1
                            continue
                        start = datetime.fromisoformat(str(record["entrada"]).replace("Z", "+00:00"))
                        end = datetime.fromisoformat(str(record["salida"]).replace("Z", "+00:00"))
                        if end < start and start.tzinfo == end.tzinfo:
                            end += timedelta(days=1)
                        hours = max(0.0, (end - start).total_seconds() / 3600)
                        worked_total += hours
                        st.markdown(
                            f"**Fichada #{record.get('id')}:** {html.escape(str(record.get('entrada') or '—'))} → "
                            f"{html.escape(str(record.get('salida') or '—'))} · {hours:.2f} hs",
                        )
                    except (TypeError, ValueError):
                        st.warning(f"La fichada #{record.get('id')} tiene un horario inválido y no se pudo calcular.")
                if planned:
                    st.caption(f"Turno esperado para {weekday}: {', '.join(str(x.get('hora_inicio')) + '–' + str(x.get('hora_fin')) for x in planned)} ({planned_hours:.2f} hs).")
                    extra = max(0.0, worked_total - planned_hours)
                    short = max(0.0, planned_hours - worked_total)
                else:
                    st.caption(f"{weekday}: no tenía un turno asignado.")
                    extra, short = worked_total, 0.0
                if records:
                    st.markdown(
                        f'<div class="argos-card"><b>{html.escape(str(employee["nombre"]))}</b> · {target_date}<br>'
                        f'Horas trabajadas: <b>{worked_total:.2f} hs</b> · Extras: <b>{extra:.2f} hs</b> · '
                        f'De menos: <b>{short:.2f} hs</b> · Fichadas abiertas: <b>{in_progress}</b></div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.warning(f"No hay fichadas para {employee['nombre']} el {target_date}.")

            st.markdown("#### Cargar un día trabajado manualmente")
            st.caption("Sirve para completar una jornada pasada que se olvidó registrar. Las horas extras se guardan en las tablas existentes.")
            with st.form("manual_workday_form"):
                col_emp, col_day = st.columns(2)
                manual_label = col_emp.selectbox("Empleado", list(by_label), key="manual_hours_employee")
                manual_date = col_day.date_input("Día trabajado", value=date.today(), max_value=date.today(), key="manual_hours_date")
                col_start, col_end = st.columns(2)
                manual_start = col_start.time_input("Entrada", key="manual_hours_start")
                manual_end = col_end.time_input("Salida", value=datetime.strptime("16:00", "%H:%M").time(), key="manual_hours_end")
                save_manual_day = st.form_submit_button("✅ Marcar día trabajado", type="primary")
            if save_manual_day:
                record_id = db_call(
                    api.registrar_jornada_manual(by_label[manual_label]["id"], manual_date.isoformat(),
                                                 manual_start.strftime("%H:%M:%S"), manual_end.strftime("%H:%M:%S"))
                )
                if record_id is not None:
                    st.session_state["_workday_query"] = (int(by_label[manual_label]["id"]), manual_date.isoformat())
                    st.success(f"Jornada registrada con ID {record_id}.")
                    st.rerun()

    with tab_highlights:
        st.info("Reproducciones de momentos destacados vinculados con las actividades y videos guardados.")
        highlight_date = st.date_input("Fecha de highlights", value=date.today(), key="highlights_date")
        highlights = db_call(api.obtener_highlights(highlight_date.isoformat()), []) or []
        if highlights:
            for item in highlights:
                employee_name = item.get("empleado") or f"ID {item.get('empleado_id', '—')}"
                title = f"🎬 {item.get('actividad') or 'Actividad'} — {employee_name} ({item.get('fecha') or 'sin fecha'})"
                with st.expander(title):
                    col_video, col_details = st.columns([2, 1])
                    with col_video:
                        if item.get("url_reproduccion"):
                            st.video(item["url_reproduccion"])
                        else:
                            st.warning("El registro está en Turso, pero el archivo no está en el almacenamiento local de esta computadora.")
                    with col_details:
                        st.markdown(
                            f"**Empleado:** {html.escape(str(employee_name))}  \n"
                            f"**Hora:** {html.escape(str(item.get('fecha') or '—'))}  \n"
                            f"**Duración:** {html.escape(str(item.get('duracion') or '—'))}"
                        )
                        st.caption(f"Inicio: {item.get('minuto_inicio') or '—'} · Fin: {item.get('minuto_fin') or '—'}")
        else:
            st.info("No hay highlights asociados a esa fecha en la base de datos.")
        videos = db_call(api.buscar_videos_recientes(), []) or []
        activities = db_call(api.obtener_actividades(highlight_date.isoformat()), []) or []
        if videos and activities:
            st.markdown("#### Asociar un clip a una actividad")
            video_map = {f"Clip #{row['id']} · {row.get('fecha') or ''}": row for row in videos}
            activity_map = {f"{row.get('tipo') or 'Actividad'} · {row.get('empleado') or 'Sin empleado'} · {row.get('inicio') or ''} · #{row['id']}": row for row in activities}
            video_label = st.selectbox("Video", list(video_map), key="highlight_video")
            activity_label = st.selectbox("Actividad", list(activity_map), key="highlight_activity")
            clip_range = _bounded_clip_range(
                f"highlight_{video_map[video_label]['id']}", _duration_seconds(video_map[video_label].get("duracion"))
            )
            save_highlight = st.button("🎬 Guardar highlight", type="primary", key="save_highlight")
            if save_highlight:
                if clip_range is None:
                    st.warning("No hay un tramo válido para guardar.")
                    return
                highlight_id = db_call(api.registrar_highlight(
                    video_map[video_label]["id"], activity_map[activity_label]["id"],
                    _format_clip_time(clip_range[0]), _format_clip_time(clip_range[1]),
                ))
                if highlight_id is not None:
                    st.success(f"Highlight vinculado con ID {highlight_id}.")
                    st.rerun()


def render_security(db_call, flash) -> None:
    st.markdown(
        '<div class="module-header"><h2>🛡️ Seguridad y Auditoría</h2>'
        "<p>Registro histórico de incidentes críticos y alertas de incumplimiento operacional.</p></div>",
        unsafe_allow_html=True,
    )
    tab_security, tab_incidents, tab_audit = st.tabs([
        "🔒 Auditar eventos de seguridad", "⚠ Alertas de incumplimientos", "📜 Auditoría del sistema",
    ])

    with tab_security:
        col_date, col_camera = st.columns(2)
        filter_events = col_date.checkbox("Filtrar por fecha", value=False, key="security_filter_events")
        event_date = col_date.date_input("Fecha", value=date.today(), key="security_event_date", disabled=not filter_events)
        cameras = db_call(api.obtener_camaras(), []) or []
        camera_options = {"Todas": None}
        camera_options.update({f"{row.get('ubicacion') or 'Cámara'} (ID {row['id']})": row["id"] for row in cameras})
        selected_camera = col_camera.selectbox("Cámara", list(camera_options), key="security_event_camera")
        events = db_call(api.obtener_eventos_seguridad(event_date.isoformat(), event_date.isoformat()) if filter_events else api.obtener_eventos_seguridad(), []) or []
        if camera_options[selected_camera] is not None:
            events = [row for row in events if row.get("camara_id") == camera_options[selected_camera]]
        st.caption("Los movimientos sospechosos se relacionan con clips y cámaras. El DDL no define una gravedad para este tipo de evento.")
        if events:
            rows = [
                {
                    "ID": row.get("id"),
                    "Cámara": row.get("camara") or "Sin cámara relacionada",
                    "Fecha del video": row.get("fecha") or "No registrada",
                    "Inicio": row.get("inicio") or "—",
                    "Fin": row.get("fin") or "—",
                    "Descripción": row.get("descripcion") or "Movimiento sospechoso",
                }
                for row in events
            ]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            st.markdown("---")
            st.subheader("📹 Reproducir evento de seguridad")
            event_labels = {
                f"{row.get('fecha') or 'Fecha no registrada'} — {row.get('descripcion') or 'Movimiento sospechoso'} (ID {row['id']})": row
                for row in events
            }
            selected_event = st.selectbox("Seleccioná el evento", list(event_labels), key="selected_security_event")
            event = event_labels[selected_event]
            col_video, col_info = st.columns([2, 1])
            with col_video:
                if event.get("url_reproduccion"):
                    st.video(event["url_reproduccion"])
                else:
                    st.warning("El evento existe en Turso, pero el archivo no está en el almacenamiento local de esta computadora.")
            with col_info:
                st.markdown(
                    f"**Cámara:** {html.escape(str(event.get('camara') or '—'))}  \n"
                    f"**Fecha:** {html.escape(str(event.get('fecha') or '—'))}  \n"
                    f"**Tramo:** {html.escape(str(event.get('inicio') or '—'))}–{html.escape(str(event.get('fin') or '—'))}"
                )
                if event.get("bounding_box"):
                    st.caption(f"Bounding box: {event['bounding_box']}")
        else:
            st.info("No hay eventos de seguridad vinculados con videos en esa fecha.")
        available_videos = db_call(api.buscar_videos_recientes(), []) or []
        if available_videos:
            st.markdown("#### Registrar un tramo de seguridad desde un clip")
            video_options = {f"Video #{row['id']} · {row.get('fecha') or ''}": row for row in available_videos}
            chosen_video = st.selectbox("Video", list(video_options), key="manual_security_video")
            event_description = st.text_input("Descripción", max_chars=500, key="manual_security_description")
            clip_range = _bounded_clip_range(
                f"security_{video_options[chosen_video]['id']}", _duration_seconds(video_options[chosen_video].get("duracion"))
            )
            save_event = st.button("🛡️ Registrar evento", type="primary", key="save_manual_security_event")
            if save_event:
                if clip_range is None:
                    st.warning("No hay un tramo válido para guardar.")
                    return
                event_id = db_call(api.registrar_evento_seguridad(
                    video_options[chosen_video]["id"], _format_clip_time(clip_range[0]),
                    _format_clip_time(clip_range[1]), event_description,
                ))
                if event_id is not None:
                    flash(f"Evento registrado con ID {event_id}.")
                    st.rerun()

    with tab_incidents:
        col_date, col_severity = st.columns(2)
        filter_alerts = col_date.checkbox("Filtrar por fecha", value=False, key="incident_filter_date")
        incident_date = col_date.date_input("Fecha", value=date.today(), key="incident_date", disabled=not filter_alerts)
        severity_filter = col_severity.selectbox("Gravedad", ["Todas", "Alta", "Media", "Baja"], key="incident_severity")
        all_alerts = db_call(api.obtener_alertas(), []) or []
        alerts = [row for row in all_alerts if not filter_alerts or str(row.get("fecha") or "")[:10] == incident_date.isoformat()]
        if severity_filter != "Todas":
            alerts = [row for row in alerts if str(row.get("grado") or "").casefold() == severity_filter.casefold()]
        st.caption("Las alertas guardan gravedad, descripción y empleado. El DDL no incluye sector ni cámara por alerta.")
        if alerts:
            st.dataframe(
                pd.DataFrame(alerts).rename(
                    columns={"id": "ID", "grado": "Gravedad", "incumplimiento": "Incumplimiento", "fecha": "Fecha y hora", "empleado": "Empleado", "empleado_id": "ID empleado"}
                ),
                use_container_width=True,
                hide_index=True,
            )
            alert_labels = {
                f"#{row['id']} · {row.get('grado') or 'Sin gravedad'} · {(row.get('empleado') or 'Empleado sin nombre')} · {row.get('fecha') or ''}": row
                for row in alerts
            }
            selected_alert = st.selectbox("Seleccioná una alerta para revisar", list(alert_labels), key="incident_review_alert")
            alert = alert_labels[selected_alert]
            review_col, comment_col = st.columns([1, 2])
            review_state = review_col.selectbox("Resultado", ["Confirmada", "Desestimada", "Pendiente"], key="incident_review_state")
            comments = comment_col.text_input("Comentarios de revisión", max_chars=1000, key="incident_review_comments")
            if st.button("Guardar revisión", type="primary", key="save_incident_review"):
                review_id = db_call(
                    api.registrar_revision_alerta(alert["id"], st.session_state.user_id, review_state, comments)
                )
                if review_id is not None:
                    flash(f"Revisión registrada con ID {review_id}.")
                    st.rerun()
            reviews = db_call(api.obtener_revisiones_alerta(alert["id"]), []) or []
            if reviews:
                st.markdown("#### Revisiones anteriores")
                st.dataframe(
                    pd.DataFrame(reviews).rename(columns={"id": "ID", "estado": "Resultado", "comentarios": "Comentarios", "fecha": "Fecha"}),
                    use_container_width=True,
                    hide_index=True,
                )
        else:
            st.info("No hay alertas para los filtros seleccionados.")

        st.markdown("---")
        with st.expander("➕ Registrar nuevo incumplimiento manualmente"):
            employees = db_call(api.obtener_empleados(incluir_inactivos=False), []) or []
            if not employees:
                st.info("Necesitás un empleado activo para asociar la alerta.")
            else:
                employee_options = {f"{row['nombre']} (ID {row['id']})": row for row in employees}
                description = st.text_area("Descripción del incumplimiento", max_chars=1000, key="manual_alert_description")
                severity = st.selectbox("Gravedad", ["Alta", "Media", "Baja"], key="manual_alert_severity")
                chosen_employee = st.selectbox("Empleado asociado", list(employee_options), key="manual_alert_employee")
                if st.button("Guardar alerta", type="primary", key="save_manual_alert"):
                    alert_id = db_call(
                        api.guardar_alerta(severity, description, employee_options[chosen_employee]["id"])
                    )
                    if alert_id is not None:
                        flash(f"Alerta registrada con ID {alert_id}.")
                        st.rerun()

    with tab_audit:
        st.markdown("#### Historial completo de auditoría")
        filter_audit = st.checkbox("Filtrar por fecha", value=False, key="audit_filter_date")
        audit_date = st.date_input("Fecha", value=date.today(), key="audit_date", disabled=not filter_audit)
        audit_rows = db_call(api.obtener_auditoria(), []) or []
        if filter_audit:
            audit_rows = [row for row in audit_rows if str(row.get("fecha") or "")[:10] == audit_date.isoformat()]
        if audit_rows:
            st.dataframe(
                pd.DataFrame(audit_rows).rename(
                    columns={"id": "ID evento", "accion": "Acción / motivo", "usuario_id": "ID usuario",
                             "usuario": "Usuario", "tabla": "Tabla", "registro_id": "ID registro afectado",
                             "fecha": "Fecha y hora"}
                ),
                use_container_width=True,
                hide_index=True,
            )
            st.caption("El esquema permite mostrar usuario_id y el nombre mediante usuario.nombre. Los registros automáticos pueden tener usuario y usuario_id vacíos; en una baja iniciada desde la app se registran ambos.")
        else:
            st.info("No hay eventos de auditoría para los filtros seleccionados.")
