import streamlit as st
import time
import pandas as pd
from datetime import date, datetime, time as dtime
import asyncio
import backend.SPs as api

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

/* ── Pantalla de login ── */
.login-wrapper {
    min-height: 85vh;
    display: flex;
    align-items: center;
    justify-content: center;
}
.login-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 2.5rem 2rem;
    width: 100%;
    max-width: 420px;
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
    # Datos en memoria (en producción vendría de BD)
    "empleados": [
        {"legajo": "EMP001", "nombre": "Juan Pérez",    "rol": "Barista",             "turno": "Mañana",  "activo": True},
        {"legajo": "EMP002", "nombre": "María Gómez",   "rol": "Cajero",              "turno": "Tarde",   "activo": True},
        {"legajo": "EMP003", "nombre": "Carlos López",  "rol": "Personal de Cocina",  "turno": "Mañana",  "activo": True},
    ],
    "turnos": [
        {"legajo": "EMP001", "nombre": "Juan Pérez",   "entrada": "08:00", "salida": "16:00", "fecha": "2026-06-18", "horas": 8},
        {"legajo": "EMP002", "nombre": "María Gómez",  "entrada": "14:00", "salida": "22:00", "fecha": "2026-06-18", "horas": 8},
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
# LOGICA ASÍNCRONA DE AUTENTICACIÓN CON HASHEO (SHA-256)
# ============================================================
async def procesar_login_async(email_usuario, password_usuario):
    """
    Se ejecuta de forma asíncrona. Hashea la clave ingresada
    y la compara con la firma criptográfica guardada en Turso.
    """
    import hashlib  # Librería nativa para triturar la contraseña
    
    # 1. Calculamos el hash de la clave ingresada eliminando espacios invisibles
    hash_clave_ingresada = hashlib.sha256(str(password_usuario).strip().encode('utf-8')).hexdigest()
    
    client = api.obtener_cliente_turso()
    try:
        query_login = "SELECT id, nombre, contrasenia FROM usuario WHERE email = ?;"
        resultado_db = await client.execute(query_login, [email_usuario])
        
        if resultado_db.rows:
            user_id = resultado_db.rows[0][0]
            user_nombre = resultado_db.rows[0][1]
            hash_db = str(resultado_db.rows[0][2]).strip()  # Hash guardado en Turso
            
            # 2. COMPARACIÓN CRIPTOGRÁFICA (Ambos ya son hashes SHA-256)
            if hash_clave_ingresada == hash_db:
                return {"valido": True, "id": user_id, "nombre": user_nombre}
                
        return {"valido": False}
    except Exception as e:
        print(f"[Turso Login Error]: {e}")
        return {"valido": False, "error": str(e)}
    finally:
        await client.close()


# ============================================================
# PANTALLA DE LOGIN CONECTADA A TURSO CLOUD
# ============================================================
if not st.session_state.autenticado:
    st.markdown('<div class="login-wrapper">', unsafe_allow_html=True)
    col_c = st.columns([1, 1.2, 1])[1]
    with col_c:
        st.markdown("""
        <div class="login-card">
            <div class="login-logo">🔒</div>
            <div class="login-title">ArgosIA</div>
            <div class="login-sub">Sistema de Monitoreo Inteligente Remoto<br>Identificación obligatoria de operador</div>
        </div>""", unsafe_allow_html=True)

        with st.container():
            usuario_mail = st.text_input("Correo Electrónico", key="usuario_input", placeholder="pablo@argosai.com")
            clave_plana = st.text_input("Contraseña", type="password", key="clave_input", placeholder="••••••••")

            if getattr(st.session_state, "_login_error", False):
                st.error("Correo electrónico o contraseña incorrectos.")
                st.session_state._login_error = False

            if st.button("Iniciar Sesión", use_container_width=True, type="primary"):
                if not usuario_mail or not clave_plana:
                    st.warning("Por favor, completa ambos campos.")
                else:
                    # Ejecutamos el flujo asíncrono pasándole los datos limpios
                    login_res = asyncio.run(procesar_login_async(usuario_mail.strip(), clave_plana.strip()))
                    
                    if login_res.get("valido"):
                        st.session_state.autenticado = True
                        st.session_state.user_nombre = login_res["nombre"]
                        st.session_state.user_id = login_res["id"]
                        st.success(f"¡Acceso Concedido! Bienvenido, {login_res['nombre']}.")
                        st.rerun()
                    else:
                        if "error" in login_res:
                            st.error(f"Fallo crítico de comunicación con la nube: {login_res['error']}")
                        else:
                            st.session_state._login_error = True
                            st.rerun()

            st.caption("El registro de nuevos operadores está sujeto a políticas de administración.")

    st.markdown('</div>', unsafe_allow_html=True)
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
    module_header("👥", "Gestión de Personal Remota", "Administración directa sobre la base de datos de Turso.")
    tab_alta, tab_lista, tab_horas = st.tabs(["➕ Alta de Personal", "📋 Ver Plantilla", "⏱ Ver Horas Extra"])
    
    with tab_alta:
        st.markdown('<div class="argos-card">', unsafe_allow_html=True)
        id_n = st.number_input("Legajo Numérico", step=1, value=50)
        nom_n = st.text_input("Nombre Completo")
        gen_n = st.selectbox("Género", ["Masculino", "Femenino", "Otro"])
        rol_n = st.selectbox("Puesto", [1, 2], help="1: Administrativo, 2: Operario")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.button("Impactar Alta Remota"):
            if not nom_n:
                st.warning("Completa el nombre completo.")
            else:
                # 🟢 CAMBIO 1: Guardado asíncrono para Turso Cloud
                asyncio.run(api.crear_empleado(
                    id_emp=id_n, 
                    nombre=nom_n, 
                    genero=gen_n, 
                    rendimiento=100.0, 
                    estado="Activo", 
                    url_imagen=f"data/biometria/emp_{id_n}", 
                    rol_id=rol_n, 
                    usuario_actual_id=st.session_state.user_id
                ))
                st.success(f"¡{nom_n} guardado en Turso Cloud!")

    with tab_lista:
        st.subheader("Plantilla Activa Obtenida de Turso")
        
        # 🟢 CAMBIO 2: Consulta asíncrona para Turso Cloud
        lista_empleados = asyncio.run(api.obtener_todos_los_empleados())
        
        if lista_empleados:
            df = pd.DataFrame(lista_empleados)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            id_b = st.number_input("ID a remover", step=1)
            if st.button("Remover Perfil", type="primary"):
                # 🟢 CAMBIO 3: Baja asíncrona para Turso Cloud
                asyncio.run(api.borrar_empleado(id_b, st.session_state.user_id))
                st.success("Registro procesado.")
                st.rerun()
        else:
            st.info("No se registran empleados activos en la base de datos.")

    with tab_horas:
        id_h = st.number_input("Consultar Horas Extra del Empleado ID", step=1, value=2)
        # 🟢 CAMBIO 4: Consulta de horas extra asíncrona
        extras = asyncio.run(api.obtener_horas_extra_empleado(id_h))
        if extras: 
            st.dataframe(pd.DataFrame(extras), use_container_width=True, hide_index=True)
        else: 
            st.info("Sin registros de horas extra calculadas para este ID.")


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
        col_emp_j, col_fecha_j = st.columns(2)
        with col_emp_j:
            emp_jornada = st.selectbox(
                "Empleado",
                [f"{e['nombre']} ({e['legajo']})" for e in st.session_state.empleados if e["activo"]],
                key="sel_jornada",
            )
        with col_fecha_j:
            fecha_j = st.date_input("Fecha a validar", value=date.today(), key="fecha_jornada")

        if st.button("🔍 Consultar jornada", type="primary"):
            legajo_j = emp_jornada.split("(")[-1].rstrip(")")
            turnos_emp = [t for t in st.session_state.turnos
                          if t["legajo"] == legajo_j and t["fecha"] == str(fecha_j)]
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
    module_header("🛡️", "Auditoría de Alertas", "Historial crítico de incidencias operacionales detectadas por visión artificial.")

    tab_seg, tab_inc = st.tabs([
        "🔒 Auditar eventos de seguridad",
        "⚠ Alertas de incumplimientos",
    ])

    # ── TAB 1: EVENTOS DE SEGURIDAD GENERALES DESDE TURSO ──
    with tab_seg:
        st.subheader("Historial de Incidencias en Tiempo Real")
        
        # 🟢 CONEXIÓN ASÍNCRONA: Consulta remota resolviendo corrutina de Turso
        alertas_db = asyncio.run(api.obtener_todas_las_alertas())
        
        if alertas_db:
            df_al = pd.DataFrame(alertas_db)
            # Reorganizamos las columnas para que se vean prolijas en tu tabla
            df_al_vis = df_al[["fechaYHora", "grado", "incumplimiento", "empleado"]].copy()
            df_al_vis.columns = ["Fecha y Hora", "Gravedad", "Incumplimiento / Alerta", "Empleado Involucrado"]
            st.dataframe(df_al_vis, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.subheader("📹 Reproducir Grabación del Evento Crítico")
            
            # Selector dinámico basado en las alertas reales de la base de datos
            opciones_alertas = [f"[ID {a['id']}] — {a['empleado']} — {a['incumplimiento']}" for a in alertas_db]
            alerta_sel = st.selectbox("Seleccioná la alerta para auditar el clip", opciones_alertas, key="sel_auditoria_al")
            
            # Buscamos los datos de la alerta seleccionada para renderizar el badge dinámico
            id_al_sel = int(alerta_sel.split("]")[0].replace("[ID ", ""))
            al_data = next(a for a in alertas_db if a["id"] == id_al_sel)
            grav_tipo = "danger" if al_data["grado"].lower() in ["alto", "crítico", "critico"] else "warning"
            
            col_iv, col_im = st.columns([2, 1])
            with col_iv:
                # Simulación de reproducción multimedia local/remota integrada
                if st.button("▶ Reproducir video del evento seleccionado", type="primary", key="btn_seg"):
                    st.video("https://w3schools.com")
            with col_im:
                st.markdown(f"""
                <div class="argos-card" style="margin-top:0;">
                    <b>Operador Actual:</b> {st.session_state.get('user_nombre', 'N/A')}<br>
                    <b>Gravedad:</b> {badge(al_data['grado'], grav_tipo)}<br>
                    <b>Fecha:</b> {al_data['fechaYHora']}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No se registran alertas operacionales críticas en el clúster de Turso Cloud.")

    # ── TAB 2: INCUMPLIMIENTOS OPERACIONALES (ALERTA MANUAL DIRECTA A TURSO) ──
    with tab_inc:
        st.subheader("Registro de Alertas y Auditorías")
        st.markdown("Utilizá este formulario para registrar un incumplimiento operacional de forma manual si las cámaras de IA se apagan.")
        
        st.markdown('<div class="argos-card">', unsafe_allow_html=True)
        col_an, col_as = st.columns(2)
        with col_an:
            nueva_desc = st.text_input("Descripción del incumplimiento (ej: Abandono de puesto)")
            nueva_grav = st.selectbox("Gravedad de la Alerta", ["Alta", "Media", "Baja"], key="ng_manual")
        with col_as:
            # Trae la lista de empleados reales de Turso para evitar ingresar IDs inválidos
            plantilla_empleados = asyncio.run(api.obtener_todos_los_empleados())
            if plantilla_empleados:
                opciones_emp_alertas = {f"{e['nombre']} (ID: {e['id']})": e['id'] for e in plantilla_empleados}
                emp_alerta_sel = st.selectbox("Asociar Incumplimiento al Empleado:", list(opciones_emp_alertas.keys()))
                id_empleado_alerta = opciones_emp_alertas[emp_alerta_sel]
            else:
                st.warning("No hay empleados en la base de datos para asociar la alerta.")
                id_empleado_alerta = None
        st.markdown('</div>', unsafe_allow_html=True)

        if st.button("Guardar Alerta Manual en la Nube", type="primary"):
            if not nueva_desc:
                st.warning("Por favor, ingresá una descripción del incumplimiento antes de guardar.")
            elif id_empleado_alerta is None:
                st.error("Acción cancelada: Se requiere un empleado válido.")
            else:
                # 🟢 CONEXIÓN ASÍNCRONA: Sube la alerta manual directo a la nube de Turso
                asyncio.run(api.guardar_alerta(
                    grado=nueva_grav,
                    incumplimiento=nueva_desc,
                    empleado_id=id_empleado_alerta
                ))
                st.success("¡Alerta registrada y cargada con éxito en Turso Cloud!")
                st.rerun()



# ============================================================
# MÓDULO 5 — MI PERFIL
# ============================================================
elif menu == "👤 Mi Perfil":
    module_header("👤", "Mi Perfil", "Información del operador y opciones de sesión.")

    _, col_p, _ = st.columns([1, 1.4, 1])
    with col_p:
        # Leemos la identidad real del operador validado en Turso Cloud
        username = st.session_state.get("user_nombre", "Operador")


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

# Encapsulamos en un contenedor seguro para blindar el aislamiento estructural del CSS
with st.container(key="contenedor_navegacion_oculta"):
    _nav_cols = st.columns(len(MENU_ITEMS))
    for _i, (_icon, _label) in enumerate(MENU_ITEMS):
        _full = f"{_icon} {_label}"
        with _nav_cols[_i]:
            if st.button(
                _full,
                key=f"nav_{_label}",
                width='stretch',  # <-- Reemplazause_container_width por esto
                type="primary" if menu == _full else "secondary",
            ):
                st.session_state.menu_actual = _full
                st.rerun()
