import tkinter as tk
from tkinter import ttk, messagebox
from controllers.rendimiento_ctrl import obtener_lista_empleados, calcular_rendimiento_empleado

# Forzamos el backend compatible con Python 3.6
import matplotlib
matplotlib.use('TkAgg')

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class AppARGOSAI:
    def __init__(self, root):
        self.root = root
        self.root.title("ARGOSAI - Consultar Rendimiento Laboral")
        self.root.geometry("900x650")  

        # Frame principal para manejar el contenido
        self.contenedor = tk.Frame(self.root, padx=20, pady=20)
        self.contenedor.pack(fill="both", expand=True)

        self.mostrar_lista_empleados()

    def mostrar_lista_empleados(self):
        """Limpia el frame y muestra la lista de empleados."""
        for widget in self.contenedor.winfo_children():
            widget.destroy()
        
        tk.Label(self.contenedor, text="Consulta de Rendimiento - Selección de Empleado", 
                 font=("Arial", 16, "bold")).pack(pady=10)
        
        # Tabla de empleados
        columnas = ("ID", "Nombre", "Rol", "Estado")
        self.tree = ttk.Treeview(self.contenedor, columns=columnas, show='headings')
        
        for col in columnas:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
        
        self.tree.pack(fill="both", expand=True, pady=10)

        # Cargar datos desde el controlador
        empleados = obtener_lista_empleados()
        for emp in empleados:
            self.tree.insert("", "end", values=(emp["id"], emp["nombre"], emp["rol"], emp["estado"]))
        
        tk.Button(self.contenedor, text="Ver Rendimiento", 
                  command=self.ver_rendimiento, bg="#4CAF50", fg="white", font=("Arial", 11, "bold")).pack(pady=10)

    def ver_rendimiento(self):
        """Muestra resultados con gráfico compatible con Python 3.6."""
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Por favor, selecciona un empleado de la lista.")
            return
        
        id_emp = self.tree.item(seleccion)["values"][0]
        datos = calcular_rendimiento_empleado(id_emp)
        
        # Limpiar el frame para mostrar los detalles
        for widget in self.contenedor.winfo_children():
            widget.destroy()
        
        tk.Label(self.contenedor, text="Detalles de Rendimiento - Empleado ID: " + str(id_emp), 
                 font=("Arial", 14, "bold")).pack(pady=5)
        
        # Layout con dos columnas
        frame_datos = tk.Frame(self.contenedor)
        frame_datos.pack(fill="both", expand=True, pady=10)
        
        # Columna Izquierda Fija
        columna_izq = tk.Frame(frame_datos, width=350)
        columna_izq.pack(side="left", fill="y", padx=10)
        columna_izq.pack_propagate(False) 
        
        # Columna Derecha para el gráfico
        columna_der = tk.Frame(frame_datos)
        columna_der.pack(side="right", fill="both", expand=True, padx=10)
        
        # Mostrar métricas resumidas (sin f-strings complejos incompatibles)
        info = "\nActividades Registradas:\n"
        info += "- Diarias: " + str(datos['diarias']) + "\n"
        info += "- Semanales: " + str(datos['semanales']) + "\n"
        info += "- Mensuales: " + str(datos['mensuales']) + "\n\n"
        info += "Historial Reciente:\n"
        
        tk.Label(columna_izq, text=info, justify="left", font=("Consolas", 12)).pack(anchor="w", pady=5)
        
        for act in datos['actividades_recientes']:
            tk.Label(columna_izq, text="- " + str(act['tipo']) + " (" + str(act['inicio']) + ")", 
                     font=("Arial", 10)).pack(anchor="w")

        # ---- GRÁFICO COMPATIBLE CON PYTHON 3.6 Y MATPLOTLIB VIEJO ----
        self.fig = Figure(figsize=(5, 4), dpi=100)
        ax = self.fig.add_subplot(111)
        
        periodos = ['Diarias', 'Semanales', 'Mensuales']
        valores = [datos['diarias'], datos['semanales'], datos['mensuales']]
        colores = ['#2196F3', '#00BCD4', '#3F51B5'] 
        
        # Dibujar las barras
        barras = ax.bar(periodos, valores, color=colores, width=0.5)
        
        # Ajustes de límites y títulos tradicionales
        limite_y = max(valores) * 1.2 if max(valores) > 0 else 10
        ax.set_ylim(0, limite_y)
        ax.set_title('Frecuencia de Actividades')
        ax.set_ylabel('Cantidad de Registros')
        
        # REEMPLAZO DE BAR_LABEL (Bucle clásico compatible con Python 3.6)
        for barra in barras:
            alto = barra.get_height()
            ax.text(barra.get_x() + barra.get_width()/2.0, alto + (limite_y * 0.02),
                    str(int(alto)), ha='center', va='bottom', fontname="Consolas", fontweight="bold")
        
        # Quitar bordes estéticos de forma tradicional
        for spine in ['top', 'right', 'left']:
            ax.spines[spine].set_visible(False)
            
        # Incrustar en Tkinter de la forma clásica para Python 3.6
        self.canvas = FigureCanvasTkAgg(self.fig, master=columna_der)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.canvas.draw()
        
        # Forzar actualización de pantalla en Tkinter
        self.root.update_idletasks()
        # ------------------------------------------------------------------

        # Botón para regresar abajo
        tk.Button(self.contenedor, text="Volver a la Lista", 
                  command=self.mostrar_lista_empleados, bg="#2196F3", fg="white", font=("Arial", 11)).pack(pady=10)