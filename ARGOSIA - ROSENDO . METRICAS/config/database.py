# config/database.py

# Simulación de Tabla: empleado (Solo datos básicos)
DB_EMPLEADOS = [
    {"id": 10, "nombre": "Martín Pérez", "puesto": "Operador Jetson"},
    {"id": 11, "nombre": "Thiago González", "puesto": "Analista IA"},
    {"id": 12, "nombre": "Gastón Krawzyck", "puesto": "Seguridad Perimetral"},
    {"id": 13, "nombre": "Rosendo Martínez", "puesto": "Infraestructura"}
]

# Simulación de Tabla: inforMetrica / actividad (Datos de rendimiento)
DB_RENDIMIENTO = {
    10: {"diario": "88%", "semanal": "82%", "mensual": "85%"},
    11: {"diario": "95%", "semanal": "90%", "mensual": "92%"},
    12: {"diario": "75%", "semanal": "78%", "mensual": "80%"},
    13: {"diario": "98%", "semanal": "96%", "mensual": "97%"}
}

# Simulación de Tabla: horas (Validar Jornada Laboral)
DB_JORNADAS = {
    10: {"entrada": "08:00:15", "salida": "16:05:30"},
    11: {"entrada": "08:30:00", "salida": "16:30:00"},
    12: {"entrada": "07:55:20", "salida": "15:50:00"},
    13: {"entrada": "08:00:00", "salida": "16:00:00"}
}