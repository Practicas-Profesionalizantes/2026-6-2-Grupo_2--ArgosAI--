import tkinter as tk
from tkinter import ttk, messagebox
# Importamos la lógica desde tu controlador
from controllers.rendimiento_ctrl import obtener_lista_empleados, calcular_rendimiento_empleado

class AppARGOSAI:
    def __init__(self, root):
        self.root = root
        self.root.title("ARGOSAI - Consultar Rendimiento Laboral")
        self.root.geometry("700x500")

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
            self.tree.column(col, width=100)
        
        self.tree.pack(fill="both", expand=True, pady=10)

        # Cargar datos desde el controlador
        empleados = obtener_lista_empleados()
        for emp in empleados:
            self.tree.insert("", "end", values=(emp["id"], emp["nombre"], emp["rol"], emp["estado"]))
        
        tk.Button(self.contenedor, text="Ver Rendimiento", 
                  command=self.ver_rendimiento, bg="#4CAF50", fg="white").pack(pady=10)

    def ver_rendimiento(self):
        """Obtiene el ID seleccionado y muestra los resultados."""
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Por favor, selecciona un empleado de la lista.")
            return
        
        id_emp = self.tree.item(seleccion[0])["values"][0]
        datos = calcular_rendimiento_empleado(id_emp)
        
        # Limpiar el frame para mostrar los detalles
        for widget in self.contenedor.winfo_children():
            widget.destroy()
        
        tk.Label(self.contenedor, text=f"Detalles de Rendimiento - Empleado ID: {id_emp}", 
                 font=("Arial", 14, "bold")).pack(pady=10)
        
        # Mostrar métricas procesadas
        info = f"""
        Puntos Totales: {datos['puntos_totales']}
        Meta Esperada: {datos['meta_objetivo']}
        Porcentaje: {datos['porcentaje_rendimiento']}%
        
        Actividades Recientes:
        """
        tk.Label(self.contenedor, text=info, justify="left", font=("Consolas", 12)).pack(pady=10)
        
        # Lista de actividades (simple)
        for act in datos['actividades_recientes']:
            tk.Label(self.contenedor, text=f"- {act['tipo']} ({act['inicio']})", 
                     font=("Arial", 10)).pack(anchor="w")

        tk.Button(self.contenedor, text="Volver a la Lista", 
                  command=self.mostrar_lista_empleados, bg="#2196F3", fg="white").pack(pady=20)