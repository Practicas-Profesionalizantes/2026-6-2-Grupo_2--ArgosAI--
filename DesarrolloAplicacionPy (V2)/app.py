import streamlit as st
import time
import pandas as pd
from datetime import date, datetime, time as dtime

# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================
st.set_page_config(
    page_title="ArgosIA",
    layout="wide",
    page_icon="🔒",
    initial_sidebar_state="collapsed",
)

# ============================================================
# ESTILOS GLOBALES
# ============================================================
st.markdown("""
<style>
/* ── Reset sidebar ── */
[data-testid="stSidebar"] { display: none !important; }

/* ── Paleta base ── */
:root {
    --bg-primary:    #0A1326;
    --bg-card:       #111E36;
    --bg-input:      #0F1B30;
    --accent:        #00C2FF;
    --accent-hover:  #33D1FF;
    --danger:        #FF4B6E;
    --warning:       #FFB740;
    --success:       #00D68F;
    --text-primary:  #E8EDF5;
    --text-muted:    #7A8BA8;
    --border:        #1E2F4A;
}

/* ── Fondo global ── */
.stApp {
    background-color: var(--bg-primary) !important;
    color: var(--text-primary) !important;
}

/* ── Espaciado inferior para el footer fijo ── */
.block-container {
    padding-bottom: 90px !important;
    padding-top: 1.5rem !important;
    max-width: 1200px !important;
}

/* ── Tarjetas ── */
.argos-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
}

/* ── Badge de estado ── */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.04em;
}
.badge-danger  { background: rgba(255,75,110,.15); color: #FF4B6E; border: 1px solid #FF4B6E; }
.badge-warning { background: rgba(255,183,64,.15);  color: #FFB740; border: 1px solid #FFB740; }
.badge-success { background: rgba(0,214,143,.15);   color: #00D68F; border: 1px solid #00D68F; }
.badge-info    { background: rgba(0,194,255,.12);   color: #00C2FF; border: 1px solid #00C2FF; }

/* ── Títulos de módulo ── */
.module-header {
    border-left: 3px solid var(--accent);
    padding-left: .75rem;
    margin-bottom: 1.25rem;
}
.module-header h2 { margin: 0; font-size: 1.5rem; color: var(--text-primary); }
.module-header p  { margin: .25rem 0 0; font-size: .85rem; color: var(--text-muted); }

/* ── Tabs ── */
[data-testid="stTabs"] button { color: var(--text-muted) !important; }
[data-testid="stTabs"] button[aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom-color: var(--accent) !important;
}

/* ── Botones ── */
.stButton > button {
    border-radius: 8px !important;
    font-size: .85rem !important;
    height: 40px !important;
    transition: all .2s ease !important;
}
.stButton > button[kind="primary"] {
    background: var(--accent) !important;
    color: var(--bg-primary) !important;
    border: none !important;
    font-weight: 700 !important;
}
.stButton > button[kind="primary"]:hover {
    background: var(--accent-hover) !important;
}
.stButton > button[kind="secondary"] {
    background: transparent !important;
    color: var(--text-muted) !important;
    border: 1px solid var(--border) !important;
}
.stButton > button[kind="secondary"]:hover {
    color: var(--accent) !important;
    border-color: var(--accent) !important;
}

/* ── Inputs ── */
.stTextInput input, .stSelectbox select, .stDateInput input {
    background: var(--bg-input) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-primary) !important;
    border-radius: 8px !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }

/* ── Info / success / error alerts ── */
[data-testid="stAlert"] { border-radius: 10px !important; }

/* ──────────────────────────────────────────────
   FOOTER FIJO
   ────────────────────────────────────────────── */
.footer-nav {
    position: fixed;
    bottom: 0; left: 0;
    width: 100%;
    background: #080F1F;
    border-top: 1px solid var(--border);
    padding: 10px 0;
    z-index: 99999;
    display: flex;
    justify-content: center;
    gap: 8px;
}
.footer-nav a {
    display: inline-flex;
    flex-direction: column;
    align-items: center;
    gap: 3px;
    padding: 6px 20px;
    border-radius: 8px;
    text-decoration: none;
    font-size: .72rem;
    font-weight: 600;
    color: var(--text-muted);
    cursor: pointer;
    transition: all .2s ease;
    border: 1px solid transparent;
}
.footer-nav a:hover   { color: var(--accent); }
.footer-nav a.active  { color: var(--accent); border-color: var(--border); background: var(--bg-card); }
.footer-nav a .icon   { font-size: 1.2rem; }

/* ── Pantalla de login ──
   (se quitó el wrapper con min-height:85vh: en Streamlit ese div
   no envuelve realmente los widgets nativos que vienen después,
   así que solo generaba un bloque vacío enorme y forzaba scroll) */
.login-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 2.5rem 2rem;
    width: 100%;
    max-width: 420px;
    margin: 6vh auto 0 auto;
}
.login-logo {
    font-size: 2.5rem;
    text-align: center;
    margin-bottom: .5rem;
}
.login-title {
    font-size: 1.5rem;
    font-weight: 700;
    text-align: center;
    color: var(--text-primary);
    margin-bottom: .25rem;
}
.login-sub {
    font-size: .8rem;
    text-align: center;
    color: var(--text-muted);
    margin-bottom: 1.75rem;
}

/* ── Perfil ── */
.profile-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 2rem;
    text-align: center;
}
.profile-avatar {
    width: 90px;
    height: 90px;
    border-radius: 50%;
    background: var(--border);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2.5rem;
    margin: 0 auto 1rem;
    border: 3px solid var(--accent);
}
.stat-box {
    background: var(--bg-input);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: .75rem 1rem;
    margin-bottom: .6rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: .85rem;
}
.stat-label { color: var(--text-muted); }
.stat-value { color: var(--text-primary); font-weight: 600; }

/* ── KPI cards ── */
.kpi-grid { display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1.25rem; }
.kpi-box {
    flex: 1 1 140px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1rem 1.25rem;
}
.kpi-value { font-size: 1.75rem; font-weight: 800; color: var(--accent); }
.kpi-label { font-size: .75rem; color: var(--text-muted); margin-top: .15rem; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# ESTADO DE SESIÓN
# ============================================================
DEFAULTS = {
    "autenticado": False,
    "menu_actual": "📺 Monitoreo",
    "usuario_input": "",
    "clave_input": "",
    # Catálogo de puestos — tabla rol_empleado(id, nombreRol, descripcion)
    "roles": [
        {"id": 1, "nombreRol": "Cajero",            "descripcion": "Atención en caja y cobro a clientes."},
        {"id": 2, "nombreRol": "Barista",            "descripcion": "Preparación de bebidas y atención de barra."},
        {"id": 3, "nombreRol": "Personal de Cocina", "descripcion": "Preparación y despacho de alimentos."},
        {"id": 4, "nombreRol": "Encargado",          "descripcion": "Supervisión general del turno y del personal."},
        {"id": 5, "nombreRol": "Seguridad",          "descripcion": "Control de accesos y vigilancia del local."},
    ],
    # Empleados — tabla empleado(id, nombre, genero, rendimiento, estado, urlImagen, rol_id)
    "empleados": [
        {"id": 1, "nombre": "Juan Pérez",   "genero": "Masculino", "rendimiento": 92.0, "estado": "Activo", "urlImagen": "", "rol_id": 2},
        {"id": 2, "nombre": "María Gómez",  "genero": "Femenino",  "rendimiento": 97.0, "estado": "Activo", "urlImagen": "", "rol_id": 1},
        {"id": 3, "nombre": "Carlos López", "genero": "Masculino", "rendimiento": 88.0, "estado": "Activo", "urlImagen": "", "rol_id": 3},
    ],
    "turnos": [
        {"empleado_id": 1, "nombre": "Juan Pérez",  "entrada": "08:00", "salida": "16:00", "fecha": "2026-06-18", "horas": 8},
        {"empleado_id": 2, "nombre": "María Gómez", "entrada": "14:00", "salida": "22:00", "fecha": "2026-06-18", "horas": 8},
    ],
    "incidentes_seg": [
        {"hora": "14:32:10", "camara": "Cam 01", "descripcion": "Ingreso no autorizado a zona restringida", "gravedad": "Alta"},
        {"hora": "09:15:44", "camara": "Cam 03", "descripcion": "Persona sin identificación en almacén",   "gravedad": "Media"},
    ],
    "incidentes_inc": [
        {"hora": "11:20:15", "camara": "Cam 02", "descripcion": "Demora crítica en despacho (>15 min)",    "sector": "Cocina",  "gravedad": "Alta"},
        {"hora": "13:45:00", "camara": "Cam 01", "descripcion": "Empleado abandona puesto sin autorización","sector": "Salón",   "gravedad": "Media"},
    ],
}

for key, val in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val


# ============================================================
# HELPERS
# ============================================================
def badge(text, tipo="info"):
    return f'<span class="badge badge-{tipo}">{text}</span>'


def module_header(icon, title, subtitle=""):
    st.markdown(f"""
    <div class="module-header">
        <h2>{icon} {title}</h2>
        {'<p>'+subtitle+'</p>' if subtitle else ''}
    </div>""", unsafe_allow_html=True)


def kpi(value, label):
    return f'<div class="kpi-box"><div class="kpi-value">{value}</div><div class="kpi-label">{label}</div></div>'


def get_rol_nombre(rol_id):
    """Busca el nombreRol correspondiente a un rol_id (FK a rol_empleado)."""
    for r in st.session_state.roles:
        if r["id"] == rol_id:
            return r["nombreRol"]
    return "—"


def next_id(lista):
    """Simula el AUTOINCREMENT de la base de datos para nuevos registros."""
    return max([x["id"] for x in lista], default=0) + 1


def verificar_credenciales():
    try:
        u = st.secrets["credentials"]["username"]
        p = st.secrets["credentials"]["password"]
    except (KeyError, FileNotFoundError):
        # Credenciales de demo cuando no existe secrets.toml
        u, p = "admin", "admin123"

    if (st.session_state.usuario_input == u and
            st.session_state.clave_input == p):
        st.session_state.autenticado = True
    else:
        st.session_state._login_error = True


# ============================================================
# PANTALLA DE LOGIN
# ============================================================
if not st.session_state.autenticado:
    col_c = st.columns([1, 1.2, 1])[1]
    with col_c:
        st.markdown("""
        <div class="login-card">
            <div class="login-logo">🔒</div>
            <div class="login-title">ArgosIA</div>
            <div class="login-sub">Sistema de Monitoreo Inteligente<br>Identificación obligatoria de operador</div>
        </div>""", unsafe_allow_html=True)

        with st.container():
            usuario = st.text_input("Usuario", key="usuario_input", placeholder="Ingrese su usuario")
            clave   = st.text_input("Contraseña", type="password", key="clave_input", placeholder="••••••••")

            if getattr(st.session_state, "_login_error", False):
                st.error("Usuario o contraseña incorrectos.")
                st.session_state._login_error = False

            st.button("Iniciar Sesión", on_click=verificar_credenciales,
                      use_container_width=True, type="primary")

            st.caption("El registro de nuevos operadores está sujeto a políticas de administración.")

    st.stop()


# ============================================================
# NAVEGACIÓN — footer visual fijo abajo
# ============================================================
MENU_ITEMS = [
    ("📺", "Monitoreo"),
    ("👥", "Empleados"),
    ("📈", "Rendimiento"),
    ("🛡️", "Seguridad"),
    ("👤", "Mi Perfil"),
]

menu = st.session_state.menu_actual

# Footer HTML visual fijo — los clics disparan los botones Streamlit ocultos via JS
nav_html = '<div class="footer-nav">'
for icon, label in MENU_ITEMS:
    full_label = f"{icon} {label}"
    active_cls = "active" if menu == full_label else ""
    nav_html += (
        f'<a class="{active_cls}" onclick="'
        f'(function(){{var btns=window.parent.document.querySelectorAll(\'button\');'
        f'for(var b of btns){{if(b.innerText.trim().includes(\'{label}\')){{b.click();break;}}}}}})();">'
        f'<span class="icon">{icon}</span>{label}</a>'
    )
nav_html += "</div>"
st.markdown(nav_html, unsafe_allow_html=True)


# ============================================================
# MÓDULO 1 — MONITOREO
# ============================================================
if menu == "📺 Monitoreo":
    module_header("📺", "Monitoreo Analítico",
                  "Procesamiento de video e identificación de actividades en el entorno comercial.")

    tab_live, tab_grabaciones = st.tabs(["▶ Actividad en tiempo real", "🗄 Ver grabaciones"])

    # ── Tab 1: Tiempo real ──
    with tab_live:
        camaras = ["Cámara 01 — Salón / Barra", "Cámara 02 — Cocina", "Cámara 03 — Almacén", "Cámara 04 — Entrada"]

        col_sel, col_status = st.columns([2, 1])
        with col_sel:
            camara_sel = st.selectbox("Cámara activa", camaras)
        with col_status:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(badge("🟢 EN VIVO", "success"), unsafe_allow_html=True)

        st.image(
            "https://images.unsplash.com/photo-1554118811-1e0d58224f24?w=900",
            caption=f"{camara_sel}  ·  {datetime.now().strftime('%H:%M:%S')}",
            use_container_width=True,
        )

        st.markdown("---")
        st.markdown("**Miniaturas — Resto de cámaras**")
        cols_thumb = st.columns(3)
        thumbs = [c for c in camaras if c != camara_sel]
        for i, col in enumerate(cols_thumb):
            if i < len(thumbs):
                with col:
                    st.image(
                        "https://images.unsplash.com/photo-1554118811-1e0d58224f24?w=300",
                        caption=thumbs[i], use_container_width=True,
                    )

    # ── Tab 2: Grabaciones ──
    with tab_grabaciones:
        col_f, col_c, col_h = st.columns([1.2, 1.2, 1])
        with col_f:
            fecha_gr = st.date_input("Fecha", value=date.today())
        with col_c:
            camara_gr = st.selectbox("Cámara", camaras, key="sel_grab")
        with col_h:
            hora_gr = st.selectbox("Franja horaria", ["00:00–06:00", "06:00–12:00", "12:00–18:00", "18:00–24:00"])

        if st.button("🔍 Buscar grabación", type="primary"):
            with st.spinner("Recuperando grabación..."):
                time.sleep(1)
            st.success(f"Grabación encontrada: {camara_gr} · {fecha_gr} · {hora_gr}")
            st.video("https://www.w3schools.com/html/mov_bbb.mp4")


# ============================================================
# MÓDULO 2 — GESTIONAR EMPLEADO
# ============================================================
elif menu == "👥 Empleados":
    module_header("👥", "Gestión de Empleados",
                  "Puestos, alta, registro de turno, actualización y baja de personal en el sistema.")

    tab_puestos, tab_alta, tab_turno, tab_editar, tab_lista = st.tabs([
        "🧩 Puestos", "➕ Alta de empleado", "🕐 Registrar turno", "✏️ Modificar empleado", "🗑 Administrar plantilla"
    ])

    # ── Tab 0: Puestos (tabla rol_empleado) ──
    with tab_puestos:
        st.markdown("#### Puestos existentes")
        df_roles = pd.DataFrame(st.session_state.roles)[["id", "nombreRol", "descripcion"]].copy()
        df_roles.columns = ["ID", "Puesto", "Descripción"]
        st.dataframe(df_roles, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("➕ Cargar nuevo puesto")
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            nombre_rol_nuevo = st.text_input("Nombre del puesto", key="nombre_rol_nuevo")
        with col_r2:
            desc_rol_nuevo = st.text_input("Descripción", key="desc_rol_nuevo")

        if st.button("💾 Guardar puesto", type="primary", key="btn_guardar_rol"):
            if not nombre_rol_nuevo.strip():
                st.warning("Ingresá el nombre del puesto.")
            elif any(r["nombreRol"].lower() == nombre_rol_nuevo.strip().lower() for r in st.session_state.roles):
                st.error(f"Ya existe un puesto llamado \"{nombre_rol_nuevo}\".")
            else:
                st.session_state.roles.append({
                    "id": next_id(st.session_state.roles),
                    "nombreRol": nombre_rol_nuevo.strip(),
                    "descripcion": desc_rol_nuevo.strip(),
                })
                st.success(f"✅ Puesto \"{nombre_rol_nuevo}\" guardado correctamente.")
                st.rerun()

    # ── Tab 1: Alta ──
    with tab_alta:
        st.markdown('<div class="argos-card">', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Datos personales y laborales")
            nombre_nuevo = st.text_input("Nombre completo", key="alta_nombre")
            genero_nuevo = st.selectbox("Género", ["Masculino", "Femenino", "Otro"], key="alta_genero")
            estado_nuevo = st.selectbox("Estado", ["Activo", "Inactivo"], key="alta_estado")

            opciones_rol = {r["nombreRol"]: r["id"] for r in st.session_state.roles}
            if opciones_rol:
                rol_nuevo_nombre = st.selectbox("Puesto asignado", list(opciones_rol.keys()), key="alta_rol")
            else:
                st.warning("No hay puestos cargados. Cargá uno en la pestaña \"Puestos\" antes de dar de alta un empleado.")
                rol_nuevo_nombre = None

        
        with col2:
            st.subheader("Perfil biométrico")
            st.caption("Suba una imagen facial nítida, de frente, con buena iluminación.")
            foto = st.file_uploader("Imagen de referencia facial (JPG / PNG)", type=["jpg", "jpeg", "png"], key="alta_foto")
            if foto:
                st.image(foto, caption="Vista previa", width=200)

        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("💾 Guardar empleado", type="primary", key="btn_guardar_empleado"):
            if not nombre_nuevo.strip():
                st.warning("Completá el nombre del empleado antes de guardar.")
            elif rol_nuevo_nombre is None:
                st.warning("No podés dar de alta un empleado sin un puesto asignado.")
            else:
                st.session_state.empleados.append({
                    "id": next_id(st.session_state.empleados),
                    "nombre": nombre_nuevo.strip(),
                    "genero": genero_nuevo,
                    "rendimiento": rendimiento_nuevo,
                    "estado": estado_nuevo,
                    "urlImagen": foto.name if foto else "",
                    "rol_id": opciones_rol[rol_nuevo_nombre],
                })
                st.success(f"✅ Empleado **{nombre_nuevo}** guardado correctamente.")
                st.balloons()

    # ── Tab 2: Registrar turno ──
    with tab_turno:
        st.markdown('<div class="argos-card">', unsafe_allow_html=True)
        empleados_activos = [e for e in st.session_state.empleados if e["estado"] == "Activo"]
        opciones_emp = {f"{e['nombre']} (ID {e['id']})": e for e in empleados_activos}

        if not opciones_emp:
            st.info("No hay empleados activos para registrar un turno.")
            emp_sel_str = None
        else:
            col_a, col_b = st.columns(2)
            with col_a:
                emp_sel_str = st.selectbox("Empleado", list(opciones_emp.keys()), key="turno_emp")
                fecha_t     = st.date_input("Fecha del turno", value=date.today(), key="turno_fecha")
            with col_b:
                hora_entrada = st.time_input("Hora de entrada", value=dtime(8, 0), key="turno_entrada")
                hora_salida  = st.time_input("Hora de salida",  value=dtime(16, 0), key="turno_salida")

            horas_trabajadas = (
                datetime.combine(date.today(), hora_salida) -
                datetime.combine(date.today(), hora_entrada)
            ).seconds / 3600
            st.info(f"⏱ Horas calculadas: **{horas_trabajadas:.1f} hs**")
        st.markdown("</div>", unsafe_allow_html=True)

        if emp_sel_str and st.button("📋 Registrar turno", type="primary", key="btn_registrar_turno"):
            emp_data = opciones_emp[emp_sel_str]
            st.session_state.turnos.append({
                "empleado_id": emp_data["id"],
                "nombre":      emp_data["nombre"],
                "entrada":     hora_entrada.strftime("%H:%M"),
                "salida":      hora_salida.strftime("%H:%M"),
                "fecha":       str(fecha_t),
                "horas":       round(horas_trabajadas, 1),
            })
            st.success(f"✅ Turno registrado para **{emp_data['nombre']}** — {fecha_t}")

        if st.session_state.turnos:
            st.markdown("#### Turnos registrados")
            df_t = pd.DataFrame(st.session_state.turnos).rename(columns={
                "empleado_id": "ID Empleado", "nombre": "Nombre", "entrada": "Entrada",
                "salida": "Salida", "fecha": "Fecha", "horas": "Horas",
            })
            st.dataframe(df_t, use_container_width=True, hide_index=True)

    # ── Tab 3: Modificar empleado ──
    with tab_editar:
        empleados_activos_ed = [e for e in st.session_state.empleados if e["estado"] == "Activo"]
        if not empleados_activos_ed:
            st.info("No hay empleados activos para modificar.")
        else:
            opciones_ed = {f"{e['nombre']} (ID {e['id']})": e for e in empleados_activos_ed}
            emp_ed_str  = st.selectbox("Seleccioná el empleado a modificar", list(opciones_ed.keys()), key="sel_editar")
            emp_ed      = opciones_ed[emp_ed_str]

            idx_ed = next(i for i, e in enumerate(st.session_state.empleados) if e["id"] == emp_ed["id"])

            st.markdown('<div class="argos-card">', unsafe_allow_html=True)
            col_ed1, col_ed2 = st.columns(2)

            GENEROS = ["Masculino", "Femenino", "Otro"]
            ESTADOS = ["Activo", "Inactivo"]
            opciones_rol_ed = {r["nombreRol"]: r["id"] for r in st.session_state.roles}
            nombres_rol = list(opciones_rol_ed.keys())

            genero_idx = GENEROS.index(emp_ed["genero"]) if emp_ed["genero"] in GENEROS else 0
            estado_idx = ESTADOS.index(emp_ed["estado"]) if emp_ed["estado"] in ESTADOS else 0
            rol_actual_nombre = get_rol_nombre(emp_ed["rol_id"])
            rol_idx = nombres_rol.index(rol_actual_nombre) if rol_actual_nombre in nombres_rol else 0

            with col_ed1:
                st.subheader("Datos personales y laborales")
                ed_nombre = st.text_input("Nombre completo", value=emp_ed["nombre"], key="ed_nombre")
                st.text_input("ID", value=str(emp_ed["id"]), disabled=True,
                              help="El ID no puede modificarse.", key="ed_id")
                ed_genero = st.selectbox("Género", GENEROS, index=genero_idx, key="ed_genero")
                ed_estado = st.selectbox("Estado", ESTADOS, index=estado_idx, key="ed_estado")
                ed_rol_nombre = st.selectbox("Puesto asignado", nombres_rol, index=rol_idx, key="ed_rol") if nombres_rol else None
                ed_rendimiento = st.number_input(
                    "Rendimiento (%)", min_value=0.0, max_value=100.0,
                    value=float(emp_ed["rendimiento"]), step=0.5, key="ed_rendimiento",
                )

            with col_ed2:
                st.subheader("Actualizar perfil biométrico")
                st.caption("Opcional: subí una nueva imagen solo si querés reemplazar la actual.")
                foto_ed = st.file_uploader("Nueva imagen facial (JPG / PNG)", type=["jpg", "jpeg", "png"], key="ed_foto")
                if foto_ed:
                    st.image(foto_ed, caption="Vista previa nueva imagen", width=200)
                else:
                    st.info("Sin cambios en el perfil biométrico.")

            st.markdown("</div>", unsafe_allow_html=True)

            if st.button("💾 Guardar cambios", type="primary", key="btn_guardar_ed"):
                if not ed_nombre.strip():
                    st.warning("El nombre no puede estar vacío.")
                else:
                    st.session_state.empleados[idx_ed]["nombre"] = ed_nombre.strip()
                    st.session_state.empleados[idx_ed]["genero"] = ed_genero
                    st.session_state.empleados[idx_ed]["estado"] = ed_estado
                    st.session_state.empleados[idx_ed]["rendimiento"] = ed_rendimiento
                    if ed_rol_nombre:
                        st.session_state.empleados[idx_ed]["rol_id"] = opciones_rol_ed[ed_rol_nombre]
                    if foto_ed:
                        st.session_state.empleados[idx_ed]["urlImagen"] = foto_ed.name
                    st.success(f"✅ Datos de **{ed_nombre}** actualizados correctamente.")

    # ── Tab 4: Administrar plantilla ──
    with tab_lista:
        st.markdown("#### Plantilla activa")
        df_emp = pd.DataFrame(st.session_state.empleados).copy()
        df_emp["Puesto"] = df_emp["rol_id"].apply(get_rol_nombre)
        df_emp_vis = df_emp[["id", "nombre", "genero", "Puesto", "rendimiento", "estado"]].copy()
        df_emp_vis.columns = ["ID", "Nombre", "Género", "Puesto", "Rendimiento", "Estado"]
        st.dataframe(df_emp_vis, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("🗑 Eliminar empleado")
        activos_baja = [e for e in st.session_state.empleados if e["estado"] == "Activo"]
        opciones_baja = {f"{e['nombre']} (ID {e['id']})": e["id"] for e in activos_baja}

        if opciones_baja:
            emp_baja = st.selectbox("Seleccioná el empleado a eliminar", list(opciones_baja.keys()), key="sel_baja")
            motivo   = st.text_input("Motivo de la baja (requerido)", key="motivo_baja")
            confirmar = st.checkbox("Confirmo que deseo eliminar este perfil del sistema", key="confirmar_baja")

            if st.button("🗑 Eliminar empleado", type="primary", key="btn_eliminar"):
                if not motivo:
                    st.warning("Ingresá el motivo de la baja.")
                elif not confirmar:
                    st.warning("Marcá la casilla de confirmación.")
                else:
                    id_baja = opciones_baja[emp_baja]
                    for e in st.session_state.empleados:
                        if e["id"] == id_baja:
                            e["estado"] = "Inactivo"
                    st.success(f"Empleado **{emp_baja}** eliminado del sistema.")
                    st.rerun()
        else:
            st.info("No hay empleados activos para eliminar.")


# ============================================================
# MÓDULO 3 — RENDIMIENTO LABORAL
# ============================================================
elif menu == "📈 Rendimiento":
    module_header("📈", "Rendimiento Laboral",
                  "Métricas de productividad, validación de jornadas y reproducción de highlights.")

    tab_metricas, tab_jornada, tab_highlights = st.tabs([
        "📊 Métricas de actividad",
        "✔ Validar jornada laboral",
        "🎬 Highlights",
    ])

    # ── Tab 1: Métricas ──
    with tab_metricas:
        # KPIs de resumen
        st.markdown("""
        <div class="kpi-grid">
            <div class="kpi-box"><div class="kpi-value">3</div><div class="kpi-label">Empleados activos</div></div>
            <div class="kpi-box"><div class="kpi-value">94%</div><div class="kpi-label">Eficiencia promedio</div></div>
            <div class="kpi-box"><div class="kpi-value">48 hs</div><div class="kpi-label">Horas registradas hoy</div></div>
            <div class="kpi-box"><div class="kpi-value">2</div><div class="kpi-label">Alertas activas</div></div>
        </div>
        """, unsafe_allow_html=True)

        data_metricas = pd.DataFrame({
            "Empleado":           ["Juan Pérez", "María Gómez", "Carlos López"],
            "Rol":                ["Barista",     "Cajero",      "Cocina"],
            "Tareas completadas": [45, 52, 38],
            "Eficiencia %":       [92, 97, 88],
            "Tiempo activo":      ["7h 12m", "7h 55m", "6h 40m"],
            "Alertas":            [0, 0, 1],
        })

        col_filtro, _ = st.columns([1, 2])
        with col_filtro:
            periodo = st.selectbox("Período", ["Hoy", "Última semana", "Último mes"])

        st.dataframe(data_metricas, use_container_width=True, hide_index=True)

    # ── Tab 2: Validar jornada ──
    with tab_jornada:
        empleados_activos_j = [e for e in st.session_state.empleados if e["estado"] == "Activo"]
        opciones_j = {f"{e['nombre']} (ID {e['id']})": e for e in empleados_activos_j}

        col_emp_j, col_fecha_j = st.columns(2)
        with col_emp_j:
            emp_jornada = st.selectbox("Empleado", list(opciones_j.keys()), key="sel_jornada") if opciones_j else None
        with col_fecha_j:
            fecha_j = st.date_input("Fecha a validar", value=date.today(), key="fecha_jornada")

        if not opciones_j:
            st.info("No hay empleados activos para validar.")
        elif st.button("🔍 Consultar jornada", type="primary"):
            id_j = opciones_j[emp_jornada]["id"]
            turnos_emp = [t for t in st.session_state.turnos
                          if t["empleado_id"] == id_j and t["fecha"] == str(fecha_j)]
            if turnos_emp:
                for t in turnos_emp:
                    st.markdown(f"""
                    <div class="argos-card">
                        <b>{t['nombre']}</b> · {t['fecha']}<br>
                        Entrada: <b>{t['entrada']}</b> &nbsp;|&nbsp; Salida: <b>{t['salida']}</b>
                        &nbsp;|&nbsp; Horas: <b>{t['horas']} hs</b>
                        &nbsp; {badge('✔ Jornada completa', 'success') if t['horas'] >= 8 else badge('⚠ Jornada incompleta', 'warning')}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning(f"No se encontraron turnos para {emp_jornada} en la fecha {fecha_j}.")

    # ── Tab 3: Highlights ──
    with tab_highlights:
        st.info("Reproducciones automáticas de momentos destacados detectados por la IA.")

        highlights = [
            {"titulo": "Mayor volumen de atención al cliente",  "hora": "12:30", "empleado": "Juan Pérez",  "duracion": "1:42"},
            {"titulo": "Tiempo récord en despacho de pedido",   "hora": "15:10", "empleado": "María Gómez", "duracion": "0:58"},
            {"titulo": "Detección de pico de actividad cocina", "hora": "13:00", "empleado": "Carlos López","duracion": "2:05"},
        ]

        col_h_sel, _ = st.columns([1.5, 1])
        with col_h_sel:
            fechaH = st.date_input("Fecha de highlights", value=date.today())

        for h in highlights:
            with st.expander(f"🎬 {h['titulo']} · {h['hora']}"):
                col_hl, col_hr = st.columns([2, 1])
                with col_hl:
                    st.video("https://www.w3schools.com/html/mov_bbb.mp4")
                with col_hr:
                    st.markdown(f"""
                    **Empleado:** {h['empleado']}  
                    **Hora:** {h['hora']}  
                    **Duración:** {h['duracion']}  
                    """)
                    st.markdown(badge("⭐ Destacado", "info"), unsafe_allow_html=True)


# ============================================================
# MÓDULO 4 — SEGURIDAD Y AUDITORÍA
# ============================================================
elif menu == "🛡️ Seguridad":
    module_header("🛡️", "Seguridad y Auditoría",
                  "Registro histórico de incidentes críticos y alertas de incumplimiento operacional.")

    tab_seg, tab_inc = st.tabs([
        "🔒 Auditar eventos de seguridad",
        "⚠ Alertas de incumplimientos",
    ])

    # ── Tab 1: Seguridad ──
    with tab_seg:
        col_fs, col_cs = st.columns([1, 1])
        with col_fs:
            fecha_seg = st.date_input("Filtrar por fecha", value=date.today(), key="fs")
        with col_cs:
            grav_seg  = st.selectbox("Gravedad", ["Todas", "Alta", "Media", "Baja"], key="gs")

        # Tabla de incidentes
        df_seg = pd.DataFrame(st.session_state.incidentes_seg)
        st.dataframe(df_seg, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("📹 Reproducir evento de seguridad")
        incidente_sel = st.selectbox(
            "Seleccioná el incidente",
            [f"{i['hora']} — {i['descripcion']}" for i in st.session_state.incidentes_seg],
            key="sel_inc_seg",
        )

        idx = next(
            (i for i, inc in enumerate(st.session_state.incidentes_seg)
             if f"{inc['hora']} — {inc['descripcion']}" == incidente_sel), 0
        )
        inc_data = st.session_state.incidentes_seg[idx]
        grav_tipo = "danger" if inc_data["gravedad"] == "Alta" else "warning"

        col_iv, col_im = st.columns([2, 1])
        with col_iv:
            if st.button("▶ Reproducir video del evento", type="primary", key="btn_seg"):
                st.video("https://www.w3schools.com/html/mov_bbb.mp4")
        with col_im:
            st.markdown(f"""
            **Cámara:** {inc_data['camara']}  
            **Hora:** {inc_data['hora']}  
            **Gravedad:** {badge(inc_data['gravedad'], grav_tipo)}  
            """, unsafe_allow_html=True)

    # ── Tab 2: Incumplimientos ──
    with tab_inc:
        col_fi, col_si = st.columns([1, 1])
        with col_fi:
            fecha_inc = st.date_input("Filtrar por fecha", value=date.today(), key="fi")
        with col_si:
            sector_f  = st.selectbox("Sector", ["Todos", "Cocina", "Salón", "Almacén", "Entrada"], key="si")

        df_inc = pd.DataFrame(st.session_state.incidentes_inc)
        st.dataframe(df_inc, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("📹 Reproducir incumplimiento operacional")
        inc_op_sel = st.selectbox(
            "Seleccioná el incidente",
            [f"{i['hora']} — {i['descripcion']}" for i in st.session_state.incidentes_inc],
            key="sel_inc_op",
        )

        idx_op = next(
            (i for i, inc in enumerate(st.session_state.incidentes_inc)
             if f"{inc['hora']} — {inc['descripcion']}" == inc_op_sel), 0
        )
        inc_op = st.session_state.incidentes_inc[idx_op]
        grav_op = "danger" if inc_op["gravedad"] == "Alta" else "warning"

        col_ov, col_om = st.columns([2, 1])
        with col_ov:
            if st.button("▶ Reproducir video del incumplimiento", type="primary", key="btn_inc"):
                st.video("https://www.w3schools.com/html/mov_bbb.mp4")
        with col_om:
            st.markdown(f"""
            **Sector:** {inc_op['sector']}  
            **Cámara:** {inc_op['camara']}  
            **Hora:** {inc_op['hora']}  
            **Gravedad:** {badge(inc_op['gravedad'], grav_op)}  
            """, unsafe_allow_html=True)

        # Botón para añadir alerta manual
        st.markdown("---")
        with st.expander("➕ Registrar nuevo incumplimiento manualmente"):
            col_an, col_as = st.columns(2)
            with col_an:
                nueva_desc   = st.text_input("Descripción del incumplimiento")
                nuevo_sector = st.selectbox("Sector", ["Cocina", "Salón", "Almacén", "Entrada"], key="ns_nuevo")
            with col_as:
                nueva_camara = st.selectbox("Cámara", ["Cam 01", "Cam 02", "Cam 03", "Cam 04"], key="nc_nuevo")
                nueva_grav   = st.selectbox("Gravedad", ["Alta", "Media", "Baja"], key="ng_nuevo")

            if st.button("Guardar alerta", type="primary"):
                if nueva_desc:
                    st.session_state.incidentes_inc.append({
                        "hora":        datetime.now().strftime("%H:%M:%S"),
                        "camara":      nueva_camara,
                        "descripcion": nueva_desc,
                        "sector":      nuevo_sector,
                        "gravedad":    nueva_grav,
                    })
                    st.success("Alerta registrada.")
                    st.rerun()
                else:
                    st.warning("Ingresá una descripción.")


# ============================================================
# MÓDULO 5 — MI PERFIL
# ============================================================
elif menu == "👤 Mi Perfil":
    module_header("👤", "Mi Perfil", "Información del operador y opciones de sesión.")

    _, col_p, _ = st.columns([1, 1.4, 1])
    with col_p:
        try:
            username = st.secrets["credentials"]["username"]
        except (KeyError, FileNotFoundError):
            username = "admin"

        st.markdown("""
        <div class="profile-card">
            <div class="profile-avatar">👤</div>
            <h3 style="margin:0 0 .25rem;">Operador del Sistema</h3>
            <p style="color:var(--text-muted); font-size:.82rem; margin:0 0 1.25rem;">
                Sesión activa
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        def stat_row(label, value):
            st.markdown(f"""
            <div class="stat-box">
                <span class="stat-label">{label}</span>
                <span class="stat-value">{value}</span>
            </div>""", unsafe_allow_html=True)

        stat_row("Usuario",          username)
        stat_row("Rol",              "Administrador Global")
        stat_row("Estación",         "Terminal Local")
        stat_row("Último acceso",    datetime.now().strftime("%d/%m/%Y %H:%M"))
        stat_row("Módulos activos",  "5 / 5")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚪 Cerrar sesión", use_container_width=True, type="primary"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# ============================================================
# BOTONES DE NAVEGACIÓN REALES — al final del DOM, ocultos
# Streamlit los renderiza aquí abajo; CSS los hace invisibles
# pero el JS del footer los puede clickear
# ============================================================
st.markdown("""
<style>
/* Oculta el último bloque horizontal que contiene los botones de nav */
div[data-testid="stMainBlockContainer"] > div > div[data-testid="stVerticalBlock"]
  > div:last-child > div[data-testid="stHorizontalBlock"] {
    opacity: 0 !important;
    height: 0 !important;
    overflow: hidden !important;
    pointer-events: none !important;
    margin: 0 !important;
    padding: 0 !important;
}
</style>
""", unsafe_allow_html=True)

_nav_cols = st.columns(len(MENU_ITEMS))
for _i, (_icon, _label) in enumerate(MENU_ITEMS):
    _full = f"{_icon} {_label}"
    with _nav_cols[_i]:
        if st.button(
            _full,
            key=f"nav_{_label}",
            use_container_width=True,
            type="primary" if menu == _full else "secondary",
        ):
            st.session_state.menu_actual = _full
            st.rerun()