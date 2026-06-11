import tkinter as tk
import datetime
from sqlalchemy import create_engine, text

# CONEXIÓN DIRECTA A LA BASE DE DATOS
DATABASE_URL = "mysql+pymysql://root:@localhost:3306/ARGOSAI"

class ArgosAIApp:
    def __init__(self, window):
        self.window = window
        self.window.title("ARGOS AI - Vista Rapida")
        self.window.geometry("650x450")
        
        try:
            self.engine = create_engine(DATABASE_URL)
            self.status_msg = "Conectado a MySQL"
        except Exception as e:
            self.status_msg = "Error de conexion"

        # --- COMPONENTES VISUALES ---
        tk.Label(window, text="PANEL DE CONTROL - ARGOS AI", font=("Arial", 14, "bold")).pack(pady=10)
        
        self.lbl_status = tk.Label(window, text=self.status_msg, fg="green", font=("Arial", 10, "italic"))
        self.lbl_status.pack()

        # Botón para refrescar manualmente
        tk.Button(window, text="ACTUALIZAR DATOS", font=("Arial", 10, "bold"), bg="#a6e3a1", command=self.cargar_datos).pack(pady=10)

        # Contenedor de Empleados
        tk.Label(window, text="Empleados Activos Ahora:", font=("Arial", 11, "bold")).pack(anchor="w", padx=20)
        self.txt_empleados = tk.Text(window, height=5, width=75)
        self.txt_empleados.pack(padx=20, pady=5)

        # Contenedor de Alertas
        tk.Label(window, text="Ultimas Alertas en BD (Identificadas por Nombre):", font=("Arial", 11, "bold")).pack(anchor="w", padx=20, pady=(10,0))
        self.txt_alertas = tk.Text(window, height=8, width=75)
        self.txt_alertas.pack(padx=20, pady=5)

        # Cargar datos por primera vez al abrir
        self.cargar_datos()

    def cargar_datos(self):
        # Borrar el texto viejo en las pantallas
        self.txt_empleados.delete("1.0", tk.END)
        self.txt_alertas.delete("1.0", tk.END)

        ahora = datetime.datetime.now()
        hora_str = ahora.strftime("%H:%M:%S")
        
        # Mapeo manual rápido del día
        dias = {0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves", 4: "Viernes", 5: "Sábado", 6: "Domingo"}
        dia_str = dias.get(ahora.weekday())

        try:
            # 1. CONSULTA DE EMPLEADOS
            query_emp = text("""
                SELECT e.id, e.nombre 
                FROM empleado e
                INNER JOIN turno t ON e.id = t.empleado_id
                INNER JOIN diasTurno dt ON t.id = dt.turno_id
                INNER JOIN diasSemana ds ON dt.diaSemana_id = ds.id
                WHERE ds.dia = :dia_actual AND :hora_actual BETWEEN t.HoraInicio AND t.HoraFin;
            """)
            
            with self.engine.connect() as con:
                empleados = con.execute(query_emp, {"dia_actual": dia_str, "hora_actual": hora_str}).fetchall()
                
                if not empleados:
                    self.txt_empleados.insert(tk.END, "No hay empleados en turno en este momento ({0} - {1}).\n".format(dia_str, hora_str))
                for emp in empleados:
                    self.txt_empleados.insert(tk.END, "- ID: {0} | Nombre: {1}\n".format(emp[0], emp[1]))

            # 2. CONSULTA DE ALERTAS CON INNER JOIN PARA TRAER EL NOMBRE
            query_alt = text("""
                SELECT a.id, a.grado, a.incumplimiento, a.fechaYHora, e.nombre 
                FROM alerta a
                INNER JOIN empleado e ON a.empleado_id = e.id
                ORDER BY a.id DESC LIMIT 5;
            """)
            
            with self.engine.connect() as con:
                alertas = con.execute(query_alt).fetchall()
                
                if not alertas:
                    self.txt_alertas.insert(tk.END, "No se registran alertas en la tabla.\n")
                for al in alertas:
                    # al[0]=id, al[1]=grado, al[2]=incumplimiento, al[3]=fecha, al[4]=nombre empleado
                    self.txt_alertas.insert(tk.END, "[ID {0}] | Empleado: {4} | Grado: {1} | {2} ({3})\n".format(
                        al[0], al[1], al[2], al[3], al[4]
                    ))

            self.lbl_status.config(text="Actualizado a las " + hora_str, fg="green")

        except Exception as e:
            self.lbl_status.config(text="Error al consultar datos", fg="red")
            self.txt_alertas.insert(tk.END, "Detalle del error: {0}".format(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = ArgosAIApp(root)
    root.mainloop()