# models/horas_model.py
from database.connection import obtener_conexion

class HorasModel:
    @staticmethod
    def obtener_horas_extra_empleado(empleado_id):
        """
        Busca y une las fichadas de entrada/salida con sus respectivas 
        horas extra calculadas para un empleado específico.
        """
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        try:
            query = """
                SELECT 
                    h.fechaYHoraEntrada, 
                    h.fechaYHoraSalida, 
                    he.cantidad
                FROM horas_extra he
                JOIN horas h ON he.horas_id = h.id
                WHERE h.empleado_id = ?
                ORDER BY h.fechaYHoraEntrada DESC;
            """
            cursor.execute(query, (empleado_id,))
            resultados = cursor.fetchall()
            return resultados
        except Exception as e:
            print(f"[❌ Error en HorasModel]: {e}")
            return []
        finally:
            conexion.close()