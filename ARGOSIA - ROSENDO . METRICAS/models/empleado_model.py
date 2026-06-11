# models/empleado_model.py
from config.database import DB_EMPLEADOS, DB_RENDIMIENTO, DB_JORNADAS

class EmpleadoModel:
    @staticmethod
    def obtener_lista_nombres():
        # Retorna solo la información básica para la primera lista
        return DB_EMPLEADOS

    @staticmethod
    def obtener_datos_rendimiento(emp_id):
        return DB_RENDIMIENTO.get(emp_id)

    @staticmethod
    def obtener_datos_jornada(emp_id):
        return DB_JORNADAS.get(emp_id)