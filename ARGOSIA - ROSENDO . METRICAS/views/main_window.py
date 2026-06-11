# views/main_window.py

import tkinter as tk

from models.empleado_model import EmpleadoModel



class ArgosiaApp(tk.Tk):

    def __init__(self):

        super().__init__()

        self.title("ARGOSIA - Gestión de Métricas y Seguridad")

        self.geometry("1000x650")

        self.configure(bg="#2d2d2d")



        # --- BARRA LATERAL (Menú Gestionar Métricas y Seguridad) ---

        self.sidebar = tk.Frame(self, bg="#1e1e1e", width=250)

        self.sidebar.pack(side="left", fill="y")

        self.sidebar.pack_propagate(False)



        tk.Label(self.sidebar, text="GESTIÓN Y SEGURIDAD", bg="#1e1e1e", fg="#00ff00",

                 font=("Arial", 12, "bold")).pack(pady=20)



        # Las 3 opciones del menú que pediste

        self.btn_rendimiento = tk.Button(self.sidebar, text="Consultar Rendimiento Laboral",

                                        command=self.vista_lista_empleados, bg="#333", fg="white",

                                        relief="flat", pady=10, cursor="hand2")

        self.btn_rendimiento.pack(fill="x", padx=10, pady=5)



        self.btn_seguridad = tk.Button(self.sidebar, text="Auditar Eventos Seguridad",

                                      state="disabled", bg="#222", fg="#666", relief="flat", pady=10)

        self.btn_seguridad.pack(fill="x", padx=10, pady=5)



        self.btn_alertas = tk.Button(self.sidebar, text="Consultar Alertas",

                                    state="disabled", bg="#222", fg="#666", relief="flat", pady=10)

        self.btn_alertas.pack(fill="x", padx=10, pady=5)



        # --- CONTENEDOR PRINCIPAL ---

        self.workspace = tk.Frame(self, bg="#2d2d2d")

        self.workspace.pack(side="right", fill="both", expand=True)



    def limpiar_workspace(self):

        for widget in self.workspace.winfo_children():

            widget.destroy()



    # PASO 1: Lista de Empleados (SOLO NOMBRES)

    def vista_lista_empleados(self):

        self.limpiar_workspace()

       

        tk.Label(self.workspace, text="Selección de Personal para Análisis",

                 bg="#2d2d2d", fg="white", font=("Arial", 16, "bold")).pack(pady=20)



        # Tabla simple solo con nombres

        frame_lista = tk.Frame(self.workspace, bg="#2d2d2d")

        frame_lista.pack(pady=10, padx=50, fill="x")



        tk.Label(frame_lista, text="ID", width=10, bg="#111", fg="white").grid(row=0, column=0, pady=2)

        tk.Label(frame_lista, text="NOMBRE COMPLETO", width=40, bg="#111", fg="white").grid(row=0, column=1, pady=2)

        tk.Label(frame_lista, text="ACCIÓN", width=15, bg="#111", fg="white").grid(row=0, column=2, pady=2)



        empleados = EmpleadoModel.obtener_lista_nombres()

        for i, emp in enumerate(empleados, start=1):

            tk.Label(frame_lista, text=emp["id"], bg="#3d3d3d", fg="white").grid(row=i, column=0, sticky="nsew", pady=1)

            tk.Label(frame_lista, text=emp["nombre"], bg="#3d3d3d", fg="white").grid(row=i, column=1, sticky="nsew", pady=1)

           

            # Al cliquear, se abre la información detallada (Paso 2)

            btn = tk.Button(frame_lista, text="Ver Métricas",

                            command=lambda id=emp["id"]: self.vista_seccion_metricas(id),

                            bg="#007acc", fg="white", relief="flat")

            btn.grid(row=i, column=2, padx=5, pady=2)



    # PASO 2: Sección de Métricas (Visualizar Actividad, Jornada y Highlights)

    def vista_seccion_metricas(self, emp_id):

        self.limpiar_workspace()

       

        # Obtenemos los nombres básicos de nuevo para el encabezado

        lista = EmpleadoModel.obtener_lista_nombres()

        nombre_emp = next(e["nombre"] for e in lista if e["id"] == emp_id)



        tk.Label(self.workspace, text=f"Panel de Métricas: {nombre_emp}",

                 bg="#2d2d2d", fg="#00ff00", font=("Arial", 18, "bold")).pack(pady=20)



        # --- SECCIÓN 1: Visualizar Métricas de Actividad ---

        rendimiento = EmpleadoModel.obtener_datos_rendimiento(emp_id)

        f1 = tk.LabelFrame(self.workspace, text="Visualizar Métricas de Actividad",

                           bg="#2d2d2d", fg="white", font=("Arial", 12, "bold"), padx=20, pady=10)

        f1.pack(fill="x", padx=40, pady=10)

       

        tk.Label(f1, text=f"Rendimiento Diario: {rendimiento['diario']}", bg="#2d2d2d", fg="white").pack(anchor="w")

        tk.Label(f1, text=f"Rendimiento Semanal: {rendimiento['semanal']}", bg="#2d2d2d", fg="white").pack(anchor="w")

        tk.Label(f1, text=f"Rendimiento Mensual: {rendimiento['mensual']}", bg="#2d2d2d", fg="white").pack(anchor="w")



        # --- SECCIÓN 2: Validar Jornada Laboral ---

        jornada = EmpleadoModel.obtener_datos_jornada(emp_id)

        f2 = tk.LabelFrame(self.workspace, text="Validar Jornada Laboral",

                           bg="#2d2d2d", fg="white", font=("Arial", 12, "bold"), padx=20, pady=10)

        f2.pack(fill="x", padx=40, pady=10)

       

        tk.Label(f2, text=f"Hora de Entrada Detectada: {jornada['entrada']}", bg="#2d2d2d", fg="white").pack(anchor="w")

        tk.Label(f2, text=f"Hora de Salida Detectada: {jornada['salida']}", bg="#2d2d2d", fg="white").pack(anchor="w")



        # --- SECCIÓN 3: Reproducir Highlights ---

        btn_highlights = tk.Button(self.workspace, text="Reproducir Highlights",

                                  bg="#b94a48", fg="white", font=("Arial", 12, "bold"),

                                  width=25, height=2, relief="flat")

        btn_highlights.pack(pady=20)



        # Botón volver

        tk.Button(self.workspace, text="Volver a la Lista", command=self.vista_lista_empleados,

                 bg="#555", fg="white", relief="flat").pack(pady=10)