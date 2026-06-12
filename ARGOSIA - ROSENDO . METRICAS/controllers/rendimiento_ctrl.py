from config.conexion import ejecutar_lectura

def obtener_lista_empleados():
    """Trae la lista de todos los empleados con su rol para la vista general."""
    query = """
        SELECT e.id, e.nombre, e.genero, e.estado, r.nombreRol, e.urlImagen
        FROM empleado e
        LEFT JOIN rol_empleado r ON e.rol_id = r.id;
    """
    empleados = ejecutar_lectura(query)
    
    lista_formateada = []
    for emp in empleados:
        lista_formateada.append({
            "id": emp[0],
            "nombre": emp[1],
            "genero": emp[2],
            "estado": emp[3],
            "rol": emp[4],
            "url_imagen": emp[5]
        })
    return lista_formateada

def calcular_rendimiento_empleado(id_empleado, meta_esperada=50):
    """Calcula el rendimiento de un empleado basándose en sus actividades."""
    
    # 1. Contar actividades
    query_actividades = "SELECT COUNT(*) FROM actividad WHERE empleado_id = ?;"
    resultado_count = ejecutar_lectura(query_actividades, (id_empleado,))
    total_actividades = resultado_count[0][0] if resultado_count else 0
    
    # 2. Calcular porcentaje
    puntos_obtenidos = total_actividades * 1
    porcentaje_rendimiento = 0
    if meta_esperada > 0:
        porcentaje_rendimiento = (puntos_obtenidos / meta_esperada) * 100
        if porcentaje_rendimiento > 100:
            porcentaje_rendimiento = 100.0

    # 3. Traer últimas actividades
    query_detalle = """
        SELECT tipoActividad, fechaYHoraComienzo, fechaYHoraFin 
        FROM actividad 
        WHERE empleado_id = ? 
        ORDER BY fechaYHoraComienzo DESC LIMIT 5;
    """
    ultimas_actividades = ejecutar_lectura(query_detalle, (id_empleado,))

    data_grafico = {
        "id_empleado": id_empleado,
        "puntos_totales": puntos_obtenidos,
        "meta_objetivo": meta_esperada,
        "porcentaje_rendimiento": round(porcentaje_rendimiento, 2),
        "actividades_recientes": [{"tipo": a[0], "inicio": a[1], "fin": a[2]} for a in ultimas_actividades]
    }
    
    return data_grafico