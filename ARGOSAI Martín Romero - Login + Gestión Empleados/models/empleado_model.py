# models/empleado_model.py
import os
import shutil
from database.connection import obtener_conexion, registrar_auditoria, BIOMETRIA_ROOT

class EmpleadoModel:
    @staticmethod
    def crear_empleado(nombre, genero, rendimiento, estado, rol_id, imagenes_origen, usuario_actual_id):
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        try:
            query = """
                INSERT INTO empleado (nombre, genero, rendimiento, estado, rol_id, urlImagen)
                VALUES (?, ?, ?, ?, ?, ?);
            """
            cursor.execute(query, (nombre, genero, rendimiento, estado, rol_id, ""))
            empleado_id = cursor.lastrowid
            
            folder_path = os.path.join(BIOMETRIA_ROOT, f"emp_{empleado_id}")
            os.makedirs(folder_path, exist_ok=True)
            
            for idx, img_path in enumerate(imagenes_origen):
                if os.path.exists(img_path):
                    ext = os.path.splitext(img_path)[1]
                    shutil.copy(img_path, os.path.join(folder_path, f"bio_{idx}{ext}"))
            
            cursor.execute("UPDATE empleado SET urlImagen = ? WHERE id = ?;", (folder_path, empleado_id))
            registrar_auditoria(cursor, "INSERT", usuario_actual_id, "empleado", empleado_id)
            
            conexion.commit()
            return True, f"Empleado registrado con ID {empleado_id}."
        except Exception as e:
            conexion.rollback()
            return False, str(e)
        finally:
            conexion.close()

    @staticmethod
    def actualizar_empleado(empleado_id, nombre, genero, rol_id, estado, usuario_actual_id):
        """Modifica de punta a punta las variables maestras de un empleado."""
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        try:
            query = """
                UPDATE empleado 
                SET nombre = ?, genero = ?, rol_id = ?, estado = ? 
                WHERE id = ?;
            """
            cursor.execute(query, (nombre, genero, rol_id, estado, empleado_id))
            registrar_auditoria(cursor, "UPDATE", usuario_actual_id, "empleado", empleado_id)
            conexion.commit()
            return True, "Datos básicos del empleado modificados con éxito."
        except Exception as e:
            conexion.rollback()
            return False, str(e)
        finally:
            conexion.close()

    @staticmethod
    def agregar_fotos_existentes(empleado_id, nuevas_imagenes, usuario_actual_id):
        """Asimila e incrementa el archivo biométrico de un usuario existente sin pisar las fotos anteriores."""
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        try:
            cursor.execute("SELECT urlImagen FROM empleado WHERE id = ?", (empleado_id,))
            res = cursor.fetchone()
            folder_path = res['urlImagen'] if (res and res['urlImagen']) else os.path.join(BIOMETRIA_ROOT, f"emp_{empleado_id}")
            os.makedirs(folder_path, exist_ok=True)
            
            # Indexar archivos actuales para determinar el offset numérico del nombre
            archivos_actuales = len([f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))])
            
            for idx, img_path in enumerate(nuevas_imagenes):
                if os.path.exists(img_path):
                    ext = os.path.splitext(img_path)[1]
                    nuevo_nombre = f"bio_{archivos_actuales + idx}{ext}"
                    shutil.copy(img_path, os.path.join(folder_path, nuevo_nombre))
            
            registrar_auditoria(cursor, "UPDATE_BIOMETRIA", usuario_actual_id, "empleado", empleado_id)
            conexion.commit()
            return True, f"Se indexaron {len(nuevas_imagenes)} nuevas imágenes."
        except Exception as e:
            conexion.rollback()
            return False, str(e)
        finally:
            conexion.close()

    @staticmethod
    def eliminar_empleado(empleado_id, usuario_actual_id):
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        try:
            cursor.execute("SELECT urlImagen FROM empleado WHERE id = ?", (empleado_id,))
            res = cursor.fetchone()
            cursor.execute("DELETE FROM empleado WHERE id = ?;", (empleado_id,))
            if res and res['urlImagen'] and os.path.exists(res['urlImagen']):
                shutil.rmtree(res['urlImagen'])
            registrar_auditoria(cursor, "DELETE", usuario_actual_id, "empleado", empleado_id)
            conexion.commit()
            return True, "Eliminación completa procesada."
        except Exception as e:
            conexion.rollback()
            return False, str(e)
        finally:
            conexion.close()

    @staticmethod
    def buscar_empleados(filtro_nombre=""):
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        query = """
            SELECT e.*, r.nombreRol 
            FROM empleado e
            LEFT JOIN rol_empleado r ON e.rol_id = r.id
            WHERE e.nombre LIKE ?;
        """
        cursor.execute(query, (f"%{filtro_nombre}%",))
        resultados = cursor.fetchall()
        conexion.close()
        return resultados