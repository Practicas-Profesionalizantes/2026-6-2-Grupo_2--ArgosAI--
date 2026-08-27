import streamlit as st
import time
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, time as dtime
import asyncio
import backend.SPs as api
import os

def run_async(coro):
  """Ejecuta corrutinas asíncronas dentro del entorno síncrono de Streamlit."""
  try:
    return asyncio.run(coro)
  except RuntimeError:
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)

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

            if st.button("Iniciar Sesión", width='stretch', type="primary"):
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
  module_header(
      "📺",
      "Monitoreo Analítico",
      "Procesamiento de video e identificación de actividades en el entorno"
      " comercial.",
  )

  tab_live, tab_grabaciones = st.tabs(
      ["▶ Actividad en tiempo real", "🗄 Ver grabaciones"]
  )

  # ── Tab 1: Tiempo real ──
  with tab_live:
    camaras = [
        "Cámara 01 — Salón / Barra",
        "Cámara 02 — Cocina",
        "Cámara 03 — Almacén",
        "Cámara 04 — Entrada",
    ]

    col_sel, col_status = st.columns([2, 1])
    with col_sel:
      camara_sel = st.selectbox("Cámara activa", camaras)
    with col_status:
      st.markdown("<br>", unsafe_allow_html=True)
      st.markdown(badge("🟢 EN VIVO", "success"), unsafe_allow_html=True)

    st.image(
        "https://images.unsplash.com/photo-1554118811-1e0d58224f24?w=900",
        caption=f"{camara_sel}  ·  {datetime.now().strftime('%H:%M:%S')}",
        width='stretch',
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
              caption=thumbs[i],
              width='stretch',
          )

  # ── Tab 2: Grabaciones ──
  with tab_grabaciones:
    col_f, col_c, col_h = st.columns([1.2, 1.2, 1])
    with col_f:
      fecha_gr = st.date_input("Fecha", value=date.today())
    with col_c:
      camara_gr = st.selectbox("Cámara", camaras, key="sel_grab")
    with col_h:
      hora_gr = st.selectbox(
          "Franja horaria",
          ["00:00–06:00", "06:00–12:00", "12:00–18:00", "18:00–24:00"],
      )

    if st.button("🔍 Buscar grabación", type="primary"):
      with st.spinner("Recuperando grabación..."):
        st.success(
            f"Grabación encontrada: {camara_gr} · {fecha_gr} · {hora_gr}"
        )
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
            st.dataframe(df, width='stretch', hide_index=True)
            
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
            st.dataframe(pd.DataFrame(extras), width='stretch', hide_index=True)
        else: 
            st.info("Sin registros de horas extra calculadas para este ID.")


# ============================================================
# MÓDULO 3 — RENDIMIENTO LABORAL
# ============================================================
elif menu == "📈 Rendimiento":
  module_header(
      "📈",
      "Rendimiento Laboral",
      "Métricas de productividad, validación de jornadas y reproducción de"
      " highlights.",
  )

  tab_metricas, tab_jornada, tab_highlights = st.tabs([
      "📊 Métricas de actividad",
      "✔ Validar jornada laboral",
      "🎬 Highlights",
  ])

  # ── Tab 1: Métricas conectadas a Turso BD ──
  with tab_metricas:
    col_filtro, _ = st.columns([1, 2])
    with col_filtro:
      periodo = st.selectbox("Período", ["Hoy", "Última semana", "Último mes"])

    # Consulta real a la base de datos
    datos_empleados, _ = run_async(api.obtener_rendimiento_y_jornada())
    alertas_db = run_async(api.obtener_todas_las_alertas())

    if datos_empleados:
      df_view = pd.DataFrame(datos_empleados)
      emp_activos = (
          len(df_view[df_view["estado"] == "Activo"])
          if "estado" in df_view.columns
          else len(df_view)
      )
      eficiencia_prom = (
          int(df_view["rendimiento"].mean())
          if "rendimiento" in df_view.columns and not df_view.empty
          else 0
      )
      alertas_act = len(alertas_db) if alertas_db else 0

      st.markdown(
          f"""
            <div class="kpi-grid">
                <div class="kpi-box"><div class="kpi-value">{emp_activos}</div><div class="kpi-label">Empleados activos</div></div>
                <div class="kpi-box"><div class="kpi-value">{eficiencia_prom}%</div><div class="kpi-label">Eficiencia promedio</div></div>
                <div class="kpi-box"><div class="kpi-value">48 hs</div><div class="kpi-label">Horas registradas</div></div>
                <div class="kpi-box"><div class="kpi-value">{alertas_act}</div><div class="kpi-label">Alertas activas</div></div>
            </div>
            """,
          unsafe_allow_html=True,
      )

      st.dataframe(df_view, width='stretch', hide_index=True)
    else:
      st.info(
          "No se encontraron métricas de rendimiento registradas en la base de"
          " datos."
      )

  # ── Tab 2: Validar jornada ──
  with tab_jornada:
    col_emp_j, col_fecha_j = st.columns(2)

    plantilla_empleados = run_async(api.obtener_todos_los_empleados())
    opciones_emp = (
        [f"{e['nombre']} (ID: {e['id']})" for e in plantilla_empleados]
        if plantilla_empleados
        else []
    )

    with col_emp_j:
      if opciones_emp:
        emp_jornada = st.selectbox("Empleado", opciones_emp, key="sel_jornada")
      else:
        st.warning("No hay empleados registrados en el sistema.")
        emp_jornada = None

    with col_fecha_j:
      fecha_j = st.date_input(
          "Fecha a validar", value=date.today(), key="fecha_jornada"
      )

    if st.button("🔍 Consultar jornada", type="primary") and emp_jornada:
      id_emp_sel = int(emp_jornada.split("ID: ")[-1].rstrip(")"))
      _, datos_jornadas = run_async(api.obtener_rendimiento_y_jornada())

      # Filtrar fichadas asociadas al empleado
      nombre_emp_limpio = emp_jornada.split(" (ID:")[0]
      jornadas_emp = (
          [j for j in datos_jornadas if j.get("empleado") == nombre_emp_limpio]
          if datos_jornadas
          else []
      )

      if jornadas_emp:
        for j in jornadas_emp:
          estado_badge = (
              badge("✔ Jornada con Marcación", "success")
              if j.get("salida") != "Sin registro"
              else badge("⚠ Marcación Incompleta", "warning")
          )
          st.markdown(
              f"""
                    <div class="argos-card">
                        <b>{j['empleado']}</b> · {fecha_j}<br>
                        Turno Teórico: <b>{j['hora_inicio']} a {j['hora_fin']}</b><br>
                        Entrada Real: <b>{j['entrada']}</b> &nbsp;|&nbsp; Salida Real: <b>{j['salida']}</b>
                        &nbsp; {estado_badge}
                    </div>
                    """,
              unsafe_allow_html=True,
          )
      else:
        st.warning(
            f"No se encontraron fichadas de jornada para {emp_jornada} en la"
            f" fecha {fecha_j}."
        )

  # ── Tab 3: Highlights ──
  with tab_highlights:
    st.info(
        "Reproducciones automáticas de momentos destacados detectados por la"
        " IA."
    )

    highlights_locales = api.listar_highlights_totales()

    col_h_sel, _ = st.columns([1.5, 1])
    with col_h_sel:
      fechaH = st.date_input("Fecha de highlights", value=date.today())

    if highlights_locales:
      for h in highlights_locales:
        with st.expander(
            f"🎬 {h['actividad']} · {h['empleado']} ({h['hora']})"
        ):
          col_hl, col_hr = st.columns([2, 1])
          with col_hl:
            st.video(h["url_reproduccion"])
          with col_hr:
            st.markdown(f"""
                        **Empleado:** {h['empleado']}  
                        **Actividad:** {h['actividad']}  
                        **Fecha:** {h['fecha']}  
                        **Hora:** {h['hora']}  
                        """)
            st.markdown(badge("⭐ Destacado", "info"), unsafe_allow_html=True)
    else:
      st.caption("No hay clips de highlights almacenados en el servidor local.")


# ============================================================
# MÓDULO 4 — SEGURIDAD Y AUDITORÍA
# ============================================================
elif menu == "🛡️ Seguridad":
  module_header(
      "🛡️",
      "Auditoría de Alertas",
      "Historial crítico de incidencias operacionales y movimientos"
      " sospechosos.",
  )

  tab_seg, tab_inc, tab_gestion = st.tabs([
      "🔒 Eventos de seguridad",
      "⚠ Cargar alerta manual",
      "🗑️ Gestión y borrado",
  ])

  # ── TAB 1: EVENTOS DE SEGURIDAD ──
  with tab_seg:
    st.subheader("Historial de Incidencias en Tiempo Real")

    try:
      alertas_db = run_async(api.obtener_todas_las_alertas())
    except Exception as e:
      st.error(f"Error al consultar alertas en Turso: {e}")
      alertas_db = []

    if alertas_db:
      df_al = pd.DataFrame(alertas_db)
      cols = df_al.columns.tolist()

      col_fecha = (
          "fechaYHora"
          if "fechaYHora" in cols
          else ("fecha" if "fecha" in cols else None)
      )
      col_grado = "grado" if "grado" in cols else None
      col_inc = "incumplimiento" if "incumplimiento" in cols else None
      col_emp = (
          "empleado"
          if "empleado" in cols
          else ("empleado_id" if "empleado_id" in cols else None)
      )

      cols_vis = [
          c for c in [col_fecha, col_grado, col_inc, col_emp] if c is not None
      ]
      st.dataframe(
          df_al[cols_vis] if cols_vis else df_al,
          use_container_width=True,
          hide_index=True,
      )

      st.markdown("---")
      st.subheader("📹 Reproducir Grabación del Evento")

      opciones_alertas = [
          f"[ID {a.get('id', 'N/A')}] — {a.get('empleado', a.get('empleado_id', 'Desc'))} — {a.get('incumplimiento', 'Sin detalle')}"
          for a in alertas_db
      ]
      alerta_sel = st.selectbox(
          "Seleccioná la alerta para auditar",
          opciones_alertas,
          key="sel_auditoria_al",
      )

      try:
        id_al_sel = int(alerta_sel.split("]")[0].replace("[ID ", ""))
        al_data = next(
            (a for a in alertas_db if a.get("id") == id_al_sel), None
        )
      except Exception:
        al_data = None

      if al_data:
        col_iv, col_im = st.columns([2, 1])
        with col_iv:
          url_v = al_data.get("url_video") or al_data.get("video_url")
          if url_v:
            st.video(url_v)
          else:
            st.info("Sin video adjunto. Mostrando transmisión de respaldo:")
            st.video("https://www.w3schools.com/html/mov_bbb.mp4")

        with col_im:
          grav_tipo = (
              "danger"
              if str(al_data.get("grado", "")).lower()
              in ["alto", "crítico", "critico"]
              else "warning"
          )
          st.markdown(
              f"""
                    <div class="argos-card" style="margin-top:0;">
                        <b>Operador:</b> {st.session_state.get('user_nombre', 'N/A')}<br>
                        <b>Gravedad:</b> {badge(al_data.get('grado', 'Media'), grav_tipo)}<br>
                        <b>Fecha:</b> {al_data.get('fechaYHora', al_data.get('fecha', 'N/A'))}
                    </div>
                    """,
              unsafe_allow_html=True,
          )
    else:
      st.info("No se registran alertas operacionales en la base de datos.")

  # ── TAB 2: CARGA MANUAL CON ADJUNTO Y LÍMITE ──
  with tab_inc:
    st.subheader("Registro Manual de Incumplimientos")
    st.markdown(
        "Ingresá alertas manualmente y adjuntá clips breves de evidencia."
    )

    st.markdown('<div class="argos-card">', unsafe_allow_html=True)
    col_an, col_as = st.columns(2)

    with col_an:
      nueva_desc = st.text_input(
          "Descripción del incumplimiento", key="input_desc_manual"
      )
      nueva_grav = st.selectbox(
          "Gravedad de la Alerta", ["Alta", "Media", "Baja"], key="ng_manual"
      )

    with col_as:
      try:
        plantilla_empleados = run_async(api.obtener_todos_los_empleados())
      except Exception:
        plantilla_empleados = []

      if plantilla_empleados:
        opciones_emp_alertas = {
            f"{e.get('nombre', 'Empleado')} (ID: {e.get('id')})": e.get("id")
            for e in plantilla_empleados
            if "id" in e
        }
        emp_alerta_sel = st.selectbox(
            "Empleado involucrado:",
            list(opciones_emp_alertas.keys()),
            key="sel_emp_al_manual",
        )
        id_empleado_alerta = opciones_emp_alertas[emp_alerta_sel]
      else:
        st.warning("No hay empleados registrados.")
        id_empleado_alerta = None

    st.markdown("---")
    st.markdown("**Adjuntar evidencia multimedia**")
    archivo_v = st.file_uploader(
        "Seleccionar video (Máximo 50 MB / ~2 minutos)",
        type=["mp4", "avi", "mkv", "mov"],
        key="file_al_manual",
    )

    # Validación de límite de tamaño (50 MB)
    video_valido = True
    if archivo_v is not None:
      tamano_mb = archivo_v.size / (1024 * 1024)
      if tamano_mb > 50:
        st.error(
            f"El archivo pesa {tamano_mb:.1f} MB. Excede el límite máximo"
            " permitido de 50 MB."
        )
        video_valido = False
      else:
        st.caption(
            f"✔ Clip listo para cargar ({tamano_mb:.1f} MB). Duración estimada:"
            " < 2 min."
        )

    st.markdown("</div>", unsafe_allow_html=True)

    if st.button(
        "Guardar Alerta Manual", type="primary", key="btn_guardar_al_manual"
    ):
      if not nueva_desc.strip():
        st.warning("Ingresá una descripción antes de guardar.")
      elif id_empleado_alerta is None:
        st.error("Se requiere asociar un empleado válido.")
      elif not video_valido:
        st.error("Corregí el archivo adjunto antes de continuar.")
      else:
        url_video_final = None

        if archivo_v is not None:
          os.makedirs("./data/highlights_media_bd", exist_ok=True)
          nombre_archivo = f"manual_{id_empleado_alerta}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
          ruta_destino = os.path.join(
              "./data/highlights_media_bd", nombre_archivo
          )

          with open(ruta_destino, "wb") as f:
            f.write(archivo_v.getbuffer())

          url_video_final = (
              f"http://localhost:8000/static/videos/{nombre_archivo}"
          )

        try:
          run_async(
              api.guardar_alerta(
                  grado=nueva_grav,
                  incumplimiento=nueva_desc,
                  empleado_id=id_empleado_alerta,
                  url_video=url_video_final,
              )
          )
          st.success("¡Alerta cargada con éxito en Turso Cloud!")
          st.rerun()
        except Exception as e:
          st.error(f"Error al guardar alerta: {e}")

  # ── TAB 3: BORRADO Y GESTIÓN DE REGISTROS ──
  with tab_gestion:
    st.subheader("Administración de Registros")
    st.markdown(
        "Eliminación manual de alertas de seguridad y movimientos sospechosos"
        " obsoletos."
    )

    col_del_al, col_del_mov = st.columns(2)

    # Depuración de Alertas
    with col_del_al:
      st.markdown('<div class="argos-card">', unsafe_allow_html=True)
      st.markdown("<b>Borrar Alerta de Seguridad</b>", unsafe_allow_html=True)
      try:
        alertas_para_borrar = run_async(api.obtener_todas_las_alertas())
      except Exception:
        alertas_para_borrar = []

      if alertas_para_borrar:
        dict_del_al = {
            f"ID {a['id']} — {a.get('incumplimiento', 'Alerta')}"
            f" ({a.get('empleado', 'N/A')})": a["id"]
            for a in alertas_para_borrar
            if "id" in a
        }
        al_del_sel = st.selectbox(
            "Seleccionar alerta a eliminar:",
            list(dict_del_al.keys()),
            key="sel_del_al",
        )
        id_al_borrar = dict_del_al[al_del_sel]

        if st.button(
            "🗑️ Eliminar Alerta", type="primary", key="btn_confirm_del_al"
        ):
          try:
            if hasattr(api, "eliminar_alerta"):
              run_async(api.eliminar_alerta(id_al_borrar))
            elif hasattr(api, "borrar_alerta"):
              run_async(api.borrar_alerta(id_al_borrar))
            else:
              st.error("No existe la función de borrado en SPs.py.")
            st.success(f"Alerta ID {id_al_borrar} eliminada.")
            st.rerun()
          except Exception as e:
            st.error(f"Error al eliminar la alerta: {e}")
      else:
        st.info("No hay alertas disponibles para borrar.")
      st.markdown("</div>", unsafe_allow_html=True)

    # Depuración de Movimientos Sospechosos
    with col_del_mov:
      st.markdown('<div class="argos-card">', unsafe_allow_html=True)
      st.markdown(
          "<b>Borrar Movimiento Sospechoso / Highlight</b>",
          unsafe_allow_html=True,
      )

      movs_locales = (
          api.listar_highlights_totales()
          if hasattr(api, "listar_highlights_totales")
          else []
      )

      if movs_locales:
        dict_del_mov = {
            f"{m.get('actividad', 'Movimiento')} — {m.get('empleado', 'N/A')}"
            f" ({m.get('hora', '')})": m
            for m in movs_locales
        }
        mov_del_sel = st.selectbox(
            "Seleccionar movimiento:",
            list(dict_del_mov.keys()),
            key="sel_del_mov",
        )
        mov_obj = dict_del_mov[mov_del_sel]

        if st.button(
            "🗑️ Eliminar Movimiento", type="primary", key="btn_confirm_del_mov"
        ):
          try:
            if hasattr(api, "eliminar_movimiento"):
              run_async(
                  api.eliminar_movimiento(mov_obj.get("id", mov_del_sel))
              )
            elif hasattr(api, "borrar_highlight"):
              run_async(api.borrar_highlight(mov_obj.get("id", mov_del_sel)))
            else:
              st.info(
                  "Registro descartado del panel (asegurate de implementar"
                  " borrar_highlight en SPs.py para persistencia)."
              )
            st.success("Movimiento eliminado correctamente.")
            st.rerun()
          except Exception as e:
            st.error(f"Error al eliminar el movimiento: {e}")
      else:
        st.info("No hay registros de movimientos sospechosos.")
      st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# MÓDULO 5 — MI PERFIL
# ============================================================
elif menu == "👤 Mi Perfil":
  module_header(
      "👤", "Mi Perfil", "Información del operador y opciones de sesión."
  )

  _, col_p, _ = st.columns([1, 1.4, 1])
  with col_p:
    username = st.session_state.get("user_nombre", "Operador")

    # Interpolación dinámica del nombre de usuario en la tarjeta
    st.markdown(
        f"""
        <div class="profile-card">
            <div class="profile-avatar">👤</div>
            <h3 style="margin:0 0 .25rem;">{username}</h3>
            <p style="color:var(--text-muted); font-size:.82rem; margin:0 0 1.25rem;">
                Sesión activa
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    def stat_row(label, value):
      st.markdown(
          f"""
            <div class="stat-box">
                <span class="stat-label">{label}</span>
                <span class="stat-value">{value}</span>
            </div>""",
          unsafe_allow_html=True,
      )

    stat_row("Usuario", username)
    stat_row("Rol", "Administrador Global")
    stat_row("Estación", "Terminal Local")
    stat_row("Último acceso", datetime.now().strftime("%d/%m/%Y %H:%M"))
    stat_row("Módulos activos", "5 / 5")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪 Cerrar sesión", width='stretch', type="primary"):
      # Cierre de sesión controlado (mantiene colecciones como empleados o turnos intactas)
      for key in ["user_nombre", "logged_in", "usuario_actual", "token"]:
        st.session_state.pop(key, None)
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
