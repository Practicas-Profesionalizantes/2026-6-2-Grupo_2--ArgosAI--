# models/turno_model.py
from database.connection import obtener_conexion, registrar_auditoria

class TurnoModel:
    @staticmethod
    def asignar_turno_completo(empleado_id, hora_inicio, hora_fin, descanso_inicio, descanso_fin, lista_dias_id, usuario_actual_id):
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        try:
            query_turno = """
                INSERT INTO turno (HoraInicio, HoraFin, DescansoInicio, DescansoFin, empleado_id) 
                VALUES (?, ?, ?, ?, ?);
            """
            cursor.execute(query_turno, (hora_inicio, hora_fin, descanso_inicio, descanso_fin, empleado_id))
            id_turno = cursor.lastrowid
            
            query_relacion = "INSERT INTO diasTurno (turno_id, diaSemana_id) VALUES (?, ?);"
            for dia_id in lista_dias_id:
                cursor.execute(query_relacion, (id_turno, dia_id))
                
            registrar_auditoria(cursor, "INSERT", usuario_actual_id, "turno", id_turno)
            conexion.commit()
            return True, "Turno y descanso configurados."
        except Exception as e:
            conexion.rollback()
            return False, str(e)
        finally:
            conexion.close()

    @staticmethod
    def actualizar_horarios_turno(turno_id, hora_inicio, hora_fin, descanso_inicio, descanso_fin, usuario_actual_id):
        """Modifica directamente los marcos temporales de un turno específico y sus descansos."""
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        try:
            query = """
                UPDATE turno 
                SET HoraInicio = ?, HoraFin = ?, DescansoInicio = ?, DescansoFin = ? 
                WHERE id = ?;
            """
            cursor.execute(query, (hora_inicio, hora_fin, descanso_inicio, descanso_fin, turno_id))
            registrar_auditoria(cursor, "UPDATE", usuario_actual_id, "turno", turno_id)
            conexion.commit()
            return True, "Turno y descanso modificados con éxito."
        except Exception as e:
            conexion.rollback()
            return False, str(e)
        finally:
            conexion.close()

    @staticmethod
    def obtener_turnos_por_empleado(empleado_id):
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        query = """
            SELECT t.id, t.HoraInicio, t.HoraFin, t.DescansoInicio, t.DescansoFin, group_concat(d.dia, ', ') as dias
            FROM turno t
            JOIN diasTurno dt ON t.id = dt.turno_id
            JOIN diasSemana d ON dt.diaSemana_id = d.id
            WHERE t.empleado_id = ?
            GROUP BY t.id;
        """
        cursor.execute(query, (empleado_id,))
        filas = cursor.fetchall()
        conexion.close()
        return filas