import os
import streamlit as st
import time
import pandas as pd
import asyncio
import sys
import hashlib
from pathlib import Path
from datetime import date, datetime, time as dtime

# ============================================================
# INYECTOR DE RUTAS DINÁMICO
# ============================================================
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

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

.login-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 2.5rem 2rem;
    width: 100%;
    max-width: 420px;
    margin: 6vh auto 0 auto;
}
.login-logo { font-size: 2.5rem; text-align: center; margin-bottom: .5rem; }
.login-title { font-size: 1.5rem; font-weight: 700; text-align: center; color: var(--text-primary); margin-bottom: .25rem; }
.login-sub { font-size: .8rem; text-align: center; color: var(--text-muted); margin-bottom: 1.75rem; }

/* ── Perfil ── */
.profile-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 16px; padding: 2rem; text-align: center; }
.profile-avatar { width: 90px; height: 90px; border-radius: 50%; background: var(--border); display: flex; align-items: center; justify-content: center; font-size: 2.5rem; margin: 0 auto 1rem; border: 3px solid var(--accent); }
.stat-box { background: var(--bg-input); border: 1px solid var(--border); border-radius: 10px; padding: .75rem 1rem; margin-bottom: .6rem; display: flex; justify-content: space-between; align-items: center; font-size: .85rem; }
.stat-label { color: var(--text-muted); }
.stat-value { color: var(--text-primary); font-weight: 600; }

/* ── KPI cards ── */
.kpi-grid { display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1.25rem; }
.kpi-box { flex: 1 1 140px; background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 1rem 1.25rem; }
.kpi-value { font-size: 1.75rem; font-weight: 800; color: var(--accent); }
.kpi-label { font-size: .75rem; color: var(--text-muted); margin-top: .15rem; }
</style>
""", unsafe_allow_html=True)
# ============================================================
# ESTADO DE SESIÓN MAESTRO
# ============================================================
if "autenticado" not in st.session_state: st.session_state.autenticado = False
if "menu_actual" not in st.session_state: st.session_state.menu_actual = "📺 Monitoreo"
if "user_nombre" not in st.session_state: st.session_state.user_nombre = "Operador"
if "user_id" not in st.session_state: st.session_state.user_id = 2

# ============================================================
# HELPERS VISUALES Y RELACIONALES
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

async def obtener_nombre_puesto_async(rol_id: int) -> str:
    """
    Consulta dinámicamente en Turso Cloud el nombre del puesto basado en su ID,
    evitando hardcodear catálogos locales en el frontend.
    """
    client = api.obtener_cliente_turso()
    try:
        query = "SELECT nombreRol FROM rol_empleado WHERE id = ?;"
        res = await client.execute(query, [int(rol_id)])
        if res.rows:
            return str(res.rows[0][0])
        return "—"
    except Exception:
        return "—"
    finally:
        await client.close()

# ============================================================
# LOGICA ASÍNCRONA DE AUTENTICACIÓN CON HASHEO (SHA-256)
# ============================================================
async def procesar_login_async(email_usuario, password_usuario):
    """
    Valida las credenciales transformando la clave ingresada en SHA-256
    y consultando de forma remota la tabla 'usuario' en Turso Cloud.
    """
    client = api.obtener_cliente_turso()
    try:
        # Calculamos la firma criptográfica para contrastar de forma segura
        hash_clave_ingresada = hashlib.sha256(str(password_usuario).strip().encode('utf-8')).hexdigest()
        
        query = "SELECT id, nombre, contrasenia FROM usuario WHERE email = ?;"
        resultado = await client.execute(query, [email_usuario.strip()])
        
        if resultado.rows:
            user_id = resultado.rows[0][0]
            user_nombre = resultado.rows[0][1]
            clave_db = resultado.rows[0][2]
            
            if hash_clave_ingresada == str(clave_db).strip():
                return {"valido": True, "id": user_id, "nombre": user_nombre}
        return {"valido": False}
    except Exception as e:
        return {"valido": False, "error": str(e)}
    finally:
        await client.close()

# ============================================================
# PANTALLA DE LOGIN CONECTADA A TURSO CLOUD
# ============================================================
if not st.session_state.autenticado:
    col_c = st.columns([1, 1.2, 1])[1]
    with col_c:
        st.markdown("""
        <div class="login-card">
            <div class="login-logo">🔒</div>
            <div class="login-title">ArgosIA</div>
            <div class="login-sub">Sistema de Monitoreo Inteligente Remoto<br>Identificación obligatoria de operador</div>
        </div>""", unsafe_allow_html=True)

        with st.container():
            usuario_mail = st.text_input("Correo Electrónico", placeholder="pablo@argosai.com")
            clave_plana = st.text_input("Contraseña", type="password", placeholder="••••••••")

            if getattr(st.session_state, "_login_error", False):
                st.error("Correo electrónico o contraseña incorrectos.")
                st.session_state._login_error = False

            if st.button("Iniciar Sesión", use_container_width=True, type="primary"):
                if not usuario_mail or not clave_plana:
                    st.warning("Por favor, completa ambos campos.")
                else:
                    login_res = asyncio.run(procesar_login_async(usuario_mail.strip(), clave_plana.strip()))
                    
                    if login_res.get("valido"):
                        st.session_state.autenticado = True
                        st.session_state.user_nombre = login_res["nombre"]
                        st.session_state.user_id = login_res["id"]
                        st.rerun()
                    else:
                        if "error" in login_res:
                            st.error(f"Fallo crítico de comunicación con la nube: {login_res['error']}")
                        else:
                            st.session_state._login_error = True
                            st.rerun()

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
            "https://unsplash.com",
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
                        "https://unsplash.com",
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
            st.video("https://w3schools.com")
# ============================================================
# MÓDULO 2 — GESTIONAR EMPLEADO (CONECTADO REAL A TURSO CLOUD)
# ============================================================
elif menu == "👥 Empleados":
    module_header("👥", "Gestión de Empleados",
                  "Puestos, alta, registro de turno y administración avanzada de plantilla biométrica remota.")

    tab_puestos, tab_alta, tab_turno, tab_lista = st.tabs([
        "🧩 Puestos", "➕ Alta de empleado", "🕐 Registrar turno", "🗑 Administrar plantilla"
    ])

    # ── Tab 0: Puestos (tabla rol_empleado en la nube) ──
    with tab_puestos:
        st.markdown("#### Puestos existentes (roles relacionales)")
        
        async def consultar_roles_seguro():
            client = api.obtener_cliente_turso()
            try:
                res = await client.execute("SELECT id, nombreRol, descripcion FROM rol_empleado;")
                return res.rows if res.rows else []
            except Exception as e:
                print(f"[Error Puestos]: {e}")
                return []
            finally:
                await client.close()

        filas_roles = asyncio.run(consultar_roles_seguro())
        
        if filas_roles:
            df_roles = pd.DataFrame(filas_roles, columns=["ID", "Puesto", "Descripción"])
            st.dataframe(df_roles, use_container_width=True, hide_index=True)
            opciones_puestos = {f"{fila[1]} (ID: {fila[0]})": fila[0] for fila in filas_roles}
        else:
            st.info("No se registran puestos cargados en la base de datos.")
            opciones_puestos = {}

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
            else:
                async def guardar_puesto_async(nom, desc):
                    client = api.obtener_cliente_turso()
                    try:
                        await client.execute("INSERT INTO rol_empleado (nombreRol, descripcion) VALUES (?, ?);", [nom, desc])
                        return {"exito": True}
                    except Exception as e:
                        return {"exito": False, "msg": str(e)}
                    finally:
                        await client.close()
                
                res_puesto = asyncio.run(guardar_puesto_async(nombre_rol_nuevo.strip(), desc_rol_nuevo.strip()))
                if res_puesto.get("exito"):
                    st.success(f"✅ Puesto \"{nombre_rol_nuevo}\" guardado correctamente en Turso Cloud.")
                    st.rerun()
                else:
                    st.error(f"Fallo al guardar puesto: {res_puesto.get('msg')}")

    # ── Tab 1: Alta de Empleado (Autoincremental + Multi-Foto con Preview) ──
    with tab_alta:
        st.markdown('<div class="argos-card">', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Datos personales y laborales")
            st.caption("ℹ️ El Legajo (ID) será autogenerado de forma incremental por la base de datos.")
            nombre_nuevo = st.text_input("Nombre completo", key="alta_nombre_input")
            genero_nuevo = st.selectbox("Género", ["Masculino", "Femenino", "Otro"], key="alta_genero_input")
            
            if opciones_puestos:
                rol_nuevo_nombre = st.selectbox("Puesto asignado", list(opciones_puestos.keys()), key="alta_rol_input")
            else:
                st.warning("Cargue los puestos de la base de datos antes de continuar.")
                rol_nuevo_nombre = None
        with col2:
            st.subheader("Perfil biométrico multi-imagen")
            st.caption("Suba una o más imágenes faciales nítidas para el entrenamiento de la IA.")
            fotos = st.file_uploader("Imágenes de referencia facial (JPG / PNG)", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key="alta_fotos_uploader")
            
            if fotos:
                st.markdown("**Vista previa de capturas seleccionadas:**")
                cols_preview = st.columns(min(len(fotos), 4))
                for idx, f in enumerate(fotos):
                    with cols_preview[idx % 4]:
                        st.image(f.getvalue(), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("💾 Guardar empleado", type="primary", key="btn_guardar_empleado"):
            if not nombre_nuevo.strip():
                st.warning("Completá el nombre del empleado antes de guardar.")
            elif rol_nuevo_nombre is None:
                st.warning("No podés dar de alta un empleado sin un puesto asignado.")
            else:
                async def registrar_empleado_automatico(nom, gen, r_id):
                    client = api.obtener_cliente_turso()
                    try:
                        query = "INSERT INTO empleado (nombre, genero, rendimiento, estado, urlImagen, rol_id) VALUES (?, ?, ?, ?, ?, ?);"
                        res = await client.execute(query, [nom, gen, 100.0, "Activo", "temporal", int(r_id)])
                        nuevo_id = res.last_insert_rowid
                        
                        folder_path = f"data/biometria/empleado_{nuevo_id}"
                        os.makedirs(folder_path, exist_ok=True)
                        
                        await client.execute("UPDATE empleado SET urlImagen = ? WHERE id = ?;", [folder_path, nuevo_id])
                        return {"exito": True, "id": nuevo_id, "folder": folder_path}
                    except Exception as e:
                        return {"exito": False, "msg": str(e)}
                    finally:
                        await client.close()

                res_alta = asyncio.run(registrar_empleado_automatico(nombre_nuevo.strip(), genero_nuevo, opciones_puestos[rol_nuevo_nombre]))
                
                if res_alta.get("exito"):
                    if fotos:
                        for idx, f in enumerate(fotos):
                            ruta_foto = Path(res_alta["folder"]) / f"rostro_{idx}_{f.name}"
                            with open(ruta_foto, "wb") as file_dest:
                                file_dest.write(f.getvalue())
                    st.success(f"✅ Empleado guardado de forma autoincremental con Legajo ID: {res_alta['id']}")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"Fallo al registrar en la nube: {res_alta.get('msg')}")
                        # ── Tab 2: Registrar turno ──
    with tab_turno:
        st.markdown('<div class="argos-card">', unsafe_allow_html=True)
        plantilla_turnos = asyncio.run(api.obtener_todos_los_empleados())
        if not plantilla_turnos:
            st.info("No hay empleados registrados para asignar turnos.")
        else:
            opciones_emp_t = {f"{e['nombre']} (ID: {e['id']})": e['id'] for e in plantilla_turnos}
            col_a, col_b = st.columns(2)
            with col_a:
                emp_sel_t = st.selectbox("Seleccioná el Empleado:", list(opciones_emp_t.keys()), key="turno_emp_sel")
                fecha_t = st.date_input("Fecha del turno", value=date.today(), key="turno_fecha")
            with col_b:
                hora_entrada = st.time_input("Hora de entrada", value=dtime(8, 0), key="turno_entrada")
                hora_salida = st.time_input("Hora de salida", value=dtime(16, 0), key="turno_salida")
                horas_trabajadas = (datetime.combine(date.today(), hora_salida) - datetime.combine(date.today(), hora_entrada)).seconds / 3600
                st.info(f"⏱ Horas calculadas: **{horas_trabajadas:.1f} hs**")
            st.markdown("</div>", unsafe_allow_html=True)

            if st.button("📋 Registrar turno", type="primary", key="btn_registrar_turno"):
                res_t = asyncio.run(api.asignar_turno_completo(
                    empleado_id=opciones_emp_t[emp_sel_t], 
                    hora_inicio=hora_entrada.strftime("%H:%M:%S"), 
                    hora_fin=hora_salida.strftime("%H:%M:%S"), 
                    descanso_inicio="12:00:00", 
                    descanso_fin="13:00:00", 
                    lista_dias_id=[1],
                    usuario_actual_id=st.session_state.user_id
                ))
                if res_t.get("exito"): 
                    st.success("Turno guardado y auditado de forma atómica en Turso Cloud.")
                else: 
                    st.error(res_t.get("mensaje", "Error al procesar el turno."))

    # ── Tab 3: Administrar plantilla (Modificación e imágenes sin bug de refresco) ──
    with tab_lista:
        st.markdown("#### Plantilla activa de la Heladería (Turso Cloud)")
        plantilla = asyncio.run(api.obtener_todos_los_empleados())
        
        if plantilla:
            df_p = pd.DataFrame(plantilla)
            df_p.columns = ["ID", "Nombre", "Género", "Rendimiento", "Estado"]
            st.dataframe(df_p, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.subheader("✏️ Panel de Modificación y Control Biométrico")
            
            opciones_gestion = {f"{e['Nombre']} (ID: {e['ID']})": e for _, e in df_p.iterrows()}
            emp_gestion_sel = st.selectbox("Seleccioná el empleado a gestionar / editar:", list(opciones_gestion.keys()), key="sb_gestion_avanzada")
            empleado_a_editar = opciones_gestion[emp_gestion_sel]
            id_mod = int(empleado_a_editar["ID"])
            
            st.markdown(f"**Gestión Activa del Legajo ID: {id_mod}**")
            st.markdown('<div class="argos-card">', unsafe_allow_html=True)
            col_m1, col_m2 = st.columns(2)
            
            with col_m1:
                nuevo_nom_mod = st.text_input("Nombre completo", value=empleado_a_editar["Nombre"], key=f"mod_nom_{id_mod}")
                nuevo_gen_mod = st.selectbox("Género", ["Masculino", "Femenino", "Otro"], index=["Masculino", "Femenino", "Otro"].index(empleado_a_editar["Género"]) if empleado_a_editar["Género"] in ["Masculino", "Femenino", "Otro"] else 0, key=f"mod_gen_{id_mod}")
                nuevo_est_mod = st.selectbox("Estado", ["Activo", "Inactivo"], index=["Activo", "Inactivo"].index(empleado_a_editar["Estado"]) if empleado_a_editar["Estado"] in ["Activo", "Inactivo"] else 0, key=f"mod_est_{id_mod}")
            
            with col_m2:
                st.markdown("⚙️ **Visualizador Biométrico (SSD Local)**")
                folder_biometria = f"data/biometria/empleado_{id_mod}"
                
                if os.path.exists(folder_biometria):
                    archivos_faciales = [f for f in os.listdir(folder_biometria) if f.endswith((".jpg", ".png", ".jpeg"))]
                    if archivos_faciales:
                        st.caption(f"📁 Se detectaron {len(archivos_faciales)} imágenes guardadas para este perfil.")
                        
                        cols_galeria = st.columns(min(len(archivos_faciales), 4))
                        for idx_g, f_gal in enumerate(archivos_faciales):
                            with cols_galeria[idx_g % 4]:
                                ruta_img_g = os.path.join(folder_biometria, f_gal)
                                with open(ruta_img_g, "rb") as file_g:
                                    st.image(file_g.read(), caption=f_gal, use_container_width=True)
                                if st.button("🗑 Borrar", key=f"del_{id_mod}_{idx_g}", type="secondary"):
                                    os.remove(ruta_img_g)
                                    st.success(f"Eliminado.")
                                    st.rerun()
                    else:
                        st.info("La carpeta única del empleado no contiene imágenes biométricas.")
                else:
                    st.info("No se ha inicializado el directorio físico de imágenes de este legajo.")
                
                st.markdown("---")
                fotos_nuevas_mod = st.file_uploader("Adjuntar más imágenes a este perfil:", type=["jpg", "png", "jpeg"], accept_multiple_files=True, key=f"fotos_add_mod_{id_mod}")
            st.markdown("</div>", unsafe_allow_html=True)
            
            if st.button("💾 Guardar cambios de perfil", type="primary", key=f"btn_save_mod_changes_{id_mod}"):
                async def actualizar_empleado_async(e_id, nom, gen, est, carpeta, fotos_nuevas):
                    client = api.obtener_cliente_turso()
                    try:
                        query = "UPDATE empleado SET nombre = ?, genero = ?, estado = ?, urlImagen = ? WHERE id = ?;"
                        await client.execute(query, [nom, gen, est, carpeta, int(e_id)])
                        
                        if fotos_nuevas:
                            os.makedirs(carpeta, exist_ok=True)
                            for idx, f in enumerate(fotos_nuevas):
                                timestamp_append = datetime.now().strftime("%H%M%S")
                                ruta_append = Path(carpeta) / f"rostro_append_{timestamp_append}_{idx}_{f.name}"
                                with open(ruta_append, "wb") as f_dest:
                                    f_dest.write(f.getvalue())
                        return {"exito": True}
                    except Exception as e:
                        return {"exito": False, "msg": str(e)}
                    finally:
                        await client.close()
                        
                res_mod = asyncio.run(actualizar_empleado_async(id_mod, nuevo_nom_mod.strip(), nuevo_gen_mod, nuevo_est_mod, folder_biometria, fotos_nuevas_mod))
                if res_mod.get("exito"):
                    st.success("✅ Cambios de perfil e imágenes guardados con éxito.")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(res_mod.get("msg"))

            # ── SISTEMA DE ELIMINACIÓN Y PURGA ATÓMICA DE IMÁGENES EN DISCO ──
            st.markdown("---")
            st.subheader("🗑 Eliminar perfil de empleado")
            
            motivo = st.text_input("Motivo de la baja remota (requerido)", key=f"motivo_baja_{id_mod}")
            # 🟢 REQUERIMIENTO COMPLETO: Pregunta opcional si se desea purgar los binarios locales
            purgar_disco = st.checkbox("⚠️ Deseo eliminar también la carpeta física con todas sus imágenes de la IA", key=f"purge_disk_{id_mod}")
            confirmar = st.checkbox("Confirmo que deseo remover definitivamente este legajo de Turso Cloud", key=f"confirmar_baja_{id_mod}")

            if st.button("🗑 Eliminar empleado", type="primary", key=f"btn_eliminar_{id_mod}"):
                if not motivo:
                    st.warning("Ingresá el motivo de la baja para el registro de auditoría.")
                elif not confirmar:
                    st.warning("Marcá la casilla de confirmación.")
                else:
                    res_b = asyncio.run(api.borrar_empleado(id_mod, st.session_state.user_id))
                    if res_b.get("exito"):
                        # Si marcó la opción de purgar, barremos el directorio usando shutil de forma segura
                        if purgar_disco and os.path.exists(folder_biometria):
                            import shutil
                            try:
                                shutil.rmtree(folder_biometria)
                                st.warning(f"📁 Directorio biométrico '{folder_biometria}' borrado del almacenamiento.")
                            except Exception as e_sh:
                                print(f"[Error Shutil Purge]: {e_sh}")
                        
                        st.success(f"Empleado ID {id_mod} removido del sistema.")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(res_b["mensaje"])
        else:
            st.info("No se registran empleados activos en la base de datos remota.")


# ============================================================
# MÓDULO 3 — RENDIMIENTO LABORAL (VIDEOS DE LA IA EN VIVO)
# ============================================================
elif menu == "📈 Rendimiento":
    module_header("📈", "Rendimiento Laboral", "Métricas de productividad, validación de jornadas y reproducción de highlights.")
    tab_metricas, tab_jornada, tab_highlights = st.tabs(["📊 Métricas de actividad", "✔ Validar jornada laboral", "🎬 Highlights de la IA"])

    with tab_metricas:
        # 🟢 CORREGIDO: Encapsulamiento asíncrono para KPIs y Métricas en Rendimiento
        async def consultar_metricas_seguro():
            client = api.obtener_cliente_turso()
            try:
                res_emp = await client.execute("SELECT COUNT(*) FROM empleado WHERE estado = 'Activo';")
                res_al = await client.execute("SELECT COUNT(*) FROM alerta;")
                res_ana = await client.execute("SELECT nombre, rendimiento, estado FROM empleado;")
                
                return {
                    "activos": res_emp.rows[0][0] if res_emp.rows else 0,
                    "alertas": res_al.rows[0][0] if res_al.rows else 0,
                    "filas": res_ana.rows if res_ana.rows else []
                }
            except Exception as e:
                print(f"[Error Metricas]: {e}")
                return {"activos": 0, "alertas": 0, "filas": []}
            finally:
                await client.close()

        metricas_data = asyncio.run(consultar_metricas_seguro())

        st.markdown(f"""
        <div class="kpi-grid">
            <div class="kpi-box"><div class="kpi-value">{metricas_data['activos']}</div><div class="kpi-label">Empleados activos en DB</div></div>
            <div class="kpi-box"><div class="kpi-value">Turso</div><div class="kpi-label">Clúster AWS Activo</div></div>
            <div class="kpi-box"><div class="kpi-value">{metricas_data['alertas']}</div><div class="kpi-label">Alertas totales en la nube</div></div>
        </div>
        """, unsafe_allow_html=True)
        
        if metricas_data["filas"]:
            st.markdown("#### Resumen analítico de la plantilla")
            df_metricas = pd.DataFrame(metricas_data["filas"], columns=["Empleado", "Rendimiento asignado %", "Estado operativo"])
            st.dataframe(df_metricas, use_container_width=True, hide_index=True)
        else:
            st.info("No se registran datos analíticos de personal en Turso Cloud.")

    with tab_jornada:
        col_emp_j, col_fecha_j = st.columns(2)
        with col_emp_j:
            emp_id_j = st.number_input("Consultar Jornada por ID de Empleado", step=1, value=1, key="id_jornada_val")
        with col_fecha_j:
            fecha_j = st.date_input("Fecha a validar", value=date.today(), key="fecha_jornada")
            
        if st.button("🔍 Consultar jornada laboral", type="primary"):
            extras = asyncio.run(api.obtener_horas_extra_empleado(int(emp_id_j)))
            if extras:
                for ex in extras:
                    st.markdown(f'<div class="argos-card"><b>Fichada de Control Detectada</b><br>Entrada: {ex["entrada"]} | Salida: {ex["salida"]}<br>Horas Extra Calculadas: <b>{ex["cantidad"]} hs</b> &nbsp; {badge("✔ Verificado por Sistema", "success")}</div>', unsafe_allow_html=True)
            else:
                st.info("Sin registros de horas o fichadas calculadas en Turso Cloud para este ID.")

    with tab_highlights:
        st.info("Reproducciones automáticas de momentos destacados detectados por la IA en el local.")
        videos = api.listar_highlights_totales()
        if videos:
            for v in videos:
                with st.expander(f"🎬 {v['actividad'].upper()} — Empleado: {v['empleado']} ({v['fecha']} {v['hora']})"):
                    col_hl, col_hr = st.columns()
                    with col_hl: st.video(v["url_reproduccion"])
                    with col_hr:
                        st.markdown(f"**Archivo:** `{v['archivo']}`")
                        st.markdown(badge("⭐ Destacado por IA", "info"), unsafe_allow_html=True)
        else:
            st.info("No se registran videos analíticos en la carpeta multimedia del local.")

elif menu == "🛡️ Seguridad":
    module_header("🛡️", "Auditoría de Alertas", "Historial crítico de incumplimientos operacionales detectados por visión artificial.")
    tab_seg, tab_inc = st.tabs(["🔒 Auditar eventos de seguridad", "⚠ Alertas de incumplimientos"])

    with tab_seg:
        st.subheader("Historial de Incidencias en Tiempo Real")
        alertas = asyncio.run(api.obtener_todas_las_alertas())
        if alertas:
            df_a = pd.DataFrame(alertas)
            df_a.columns = ["ID", "Gravedad", "Incumplimiento / Alerta", "Fecha y Hora", "Empleado Involucrado"]
            st.dataframe(df_a, use_container_width=True, hide_index=True)
        else:
            st.info("Sin alertas operacionales registradas en el clúster remoto.")

    with tab_inc:
        st.subheader("Registro de Alertas Manuales")
        with st.expander("➕ Registrar nuevo incumplimiento manualmente"):
            nueva_desc = st.text_input("Descripción del incumplimiento (ej: Abandono de puesto)")
            emp_id_al = st.number_input("ID Empleado asociado", step=1, value=1, key="emp_id_alerta_man")
            nueva_grav = st.selectbox("Gravedad de la Alerta", ["Alta", "Media", "Baja"], key="ng_manual")
            
            if st.button("Guardar alerta manual", type="primary"):
                if nueva_desc:
                    asyncio.run(api.guardar_alerta(nueva_grav, nueva_desc, emp_id_al))
                    st.success("Alerta registrada y guardada de forma remota en Turso Cloud.")
                    st.rerun()
                else:
                    st.warning("Ingresá una descripción.")

elif menu == "👤 Mi Perfil":
    module_header("👤", "Mi Perfil", "Información del operador y opciones de sesión.")
    _, col_p, _ = st.columns([1, 1.4, 1])
    with col_p:
        username = st.session_state.get("user_nombre", "Operador")
        st.markdown(f'<div class="profile-card"><div class="profile-avatar">👤</div><h3 style="margin:0 0 .25rem;">{username}</h3><p style="color:var(--text-muted); font-size:.82rem; margin:0 0 1.25rem;">Sesión activa en Turso Cloud</p></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        def stat_row(label, value):
            st.markdown(f'<div class="stat-box"><span class="stat-label">{label}</span><span class="stat-value">{value}</span></div>', unsafe_allow_html=True)
        
        stat_row("Usuario ID", str(st.session_state.get("user_id", "N/A")))
        stat_row("Nombre", username)
        stat_row("Estación", "Terminal Local Cifrada")
        stat_row("Último acceso", datetime.now().strftime("%d/%m/%Y %H:%M"))
        stat_row("Módulos activos", "5 / 5")
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🚪 Cerrar sesión", use_container_width=True, type="primary"):
            st.session_state.autenticado = False
            st.rerun()

st.markdown("""<style>div[data-testid="stMainBlockContainer"] > div > div[data-testid="stVerticalBlock"] > div:last-child > div[data-testid="stHorizontalBlock"] { opacity: 0 !important; height: 0 !important; overflow: hidden !important; pointer-events: none !important; margin: 0 !important; padding: 0 !important; }</style>""", unsafe_allow_html=True)

with st.container():
    _nav_cols = st.columns(len(MENU_ITEMS))
    for _i, (_icon, _label) in enumerate(MENU_ITEMS):
        _full = f"{_icon} {_label}"
        with _nav_cols[_i]:
            if st.button(_full, key=f"nav_{_label}", use_container_width=True, type="primary" if menu == _full else "secondary"):
                st.session_state.menu_actual = _full
                st.rerun()
