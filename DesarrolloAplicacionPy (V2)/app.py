import streamlit as st
import time

# 1. Configuración de la página de escritorio (Modo ancho para paneles analíticos)
st.set_page_config(page_title="Panel de Control Inteligente", layout="wide", page_icon="🔒")

# 2. Inicializar el estado de la sesión de usuario de forma segura
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

# 3. Validación estricta del inicio de sesión único leyendo los secretos
def verificar_credenciales():
    try:
        usuario_correcto = st.secrets["credentials"]["username"]
        clave_correcta = st.secrets["credentials"]["password"]
        
        if st.session_state.usuario_input == usuario_correcto and st.session_state.clave_input == clave_correcta:
            st.session_state.autenticado = True
            st.success("¡Acceso concedido!")
        else:
            st.error("Usuario o contraseña incorrectos.")
    except KeyError:
        st.error("Error: No se encontraron las credenciales en el archivo secrets.toml")

# 4. Control del flujo visual de pantallas (Login vs Panel Principal)
if not st.session_state.autenticado:
    # --- PANTALLA DE INICIO DE SESIÓN SEGURO ---
    st.title("🔒 Sistema de Acceso Único")
    st.write("Introduce tus credenciales para acceder al panel de control de IA.")
    
    # Se crean 2 columnas equilibradas para estructurar el formulario visualmente
    col_login, _ = st.columns(2)
    with col_login:
        st.text_input("Usuario", key="usuario_input")
        st.text_input("Contraseña", type="password", key="clave_input")
        st.button("Iniciar Sesión", on_click=verificar_credenciales)
else:
    # --- PANTALLA DEL PANEL PRINCIPAL (USUARIO LOGUEADO) ---
    
    # Configuración del menú lateral del sistema
    st.sidebar.title("🎛️ Panel de Control")
    st.sidebar.write(f"Usuario activo: **{st.secrets['credentials']['username']}**")
    
    # Navegación interna entre módulos de visualización
    opcion = st.sidebar.radio("Navegación", ["Visualización de Métricas e IA", "Alertas del Sistema", "Mi Perfil"])

    st.sidebar.divider()
    
    # Bloque de cierre de sesión completamente corregido y reforzado para escritorio
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state.autenticado = False
        st.session_state.usuario_input = ""
        st.session_state.clave_input = ""
        st.rerun()

    # MÓDULO 1: VISUALIZACIÓN DE MÉMETRICAS E INTERFAZ DE IA
    if opcion == "Visualización de Métricas e IA":
        st.title("📊 Análisis de Métricas con IA")
        st.write("Visualización integrada de datos y procesamiento inteligente en tiempo real.")
        
        # Bloques flotantes de métricas críticas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Rendimiento General", value="94.2 %", delta="1.5 %")
        with col2:
            st.metric(label="Anomalías Detectadas", value="2", delta="-1", delta_color="inverse")
        with col3:
            st.metric(label="Precisión del Modelo", value="98.7 %")
            
        st.divider()
        st.subheader("🧠 Ejecución de Modelos Predictivos")
        
        # Simulación de interacción con el backend analítico
        if st.button("Procesar con IA"):
            with st.spinner("La Inteligencia Artificial de ArgosIA está analizando los patrones métricos..."):
                time.sleep(2) 
            st.success("✨ Análisis completado con éxito.")
            
            # Tabla interactiva nativa (Sin dependencias externas que rompan el sistema)
            st.write("### Datos Proyectados por el Modelo Analítico")
            st.dataframe({
                "Métrica Real": [94.2, 94.5, 93.8, 94.1, 94.2],
                "Proyección IA": [94.3, 94.8, 94.0, 94.2, 94.5]
            }, use_container_width=True)

    # MÓDULO 2: HISTORIAL DE NOTIFICACIONES Y ALERTAS
    elif opcion == "Alertas del Sistema":
        st.title("🔔 Historial de Alertas Inteligentes")
        st.write("Avisos automáticos disparados por anomalías detectadas en los flujos de datos.")
        
        st.error("🚨 **Crítica (Hace 10 min):** Se detectó un pico inusual en las métricas del servidor principal.")
        st.warning("⚠️ **Advertencia (Hace 2 horas):** La precisión del modelo predictivo descendió levemente del umbral óptimo.")
        st.info("ℹ️ **Informativa (Hoy mañana):** Sincronización de variables analíticas realizada con éxito.")

    # MÓDULO 3: PERFIL DEL ADMINISTRADOR ÚNICO
    elif opcion == "Mi Perfil":
        # Creamos dos columnas proporcionales: una muy estrecha para la foto y otra para el título grande
        col_foto, col_titulo = st.columns([1, 10])
        
        with col_foto:
            # URL directa a un avatar de prueba estable de internet
            st.image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQR9ZFmn9no38NNaTpe0CSWNkNBY_aTilsF_Q&s", width=80)
            
        with col_titulo:
            st.title("Configuración del Perfil")
            
        st.write("Información del operador único de la instancia de escritorio.")
        
        with st.expander("Ver datos completos de la cuenta", expanded=True):
            st.write(f"**Nombre de usuario:** {st.secrets['credentials']['username']}")
            st.write("**Rol en el sistema:** Administrador de Sistema Global")
            st.write("**Entorno de IA:** Conexión con Groq API configurada")