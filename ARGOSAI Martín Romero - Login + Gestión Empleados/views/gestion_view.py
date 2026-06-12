# views/gestion_view.py
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from models import EmpleadoModel, TurnoModel
from database.connection import obtener_conexion

class VentanaGestion(tk.Tk):
    def __init__(self, usuario_id, usuario_nombre):
        super().__init__()
        self.usuario_id = usuario_id
        self.title(f"ARGOSAI - Panel de Gestión [Usuario: {usuario_nombre}]")
        self.geometry("580x730")
        self.resizable(False, False)
        
        self.imagenes_seleccionadas = []
        self.turnos_temporales = []
        
        self.crear_interfaz()
        self.cargar_roles_combobox()

    def crear_interfaz(self):
        tk.Label(self, text="GESTIÓN DE EMPLEADOS", font=("Arial", 14, "bold"), fg="#1E293B").pack(pady=10)
        
        frame_form = tk.LabelFrame(self, text=" Datos del Empleado ", padx=10, pady=10)
        frame_form.pack(fill="x", padx=15, pady=5)
        
        tk.Label(frame_form, text="Nombre Completo:").grid(row=0, column=0, sticky="w", pady=4)
        self.entry_nombre = tk.Entry(frame_form, width=35)
        self.entry_nombre.grid(row=0, column=1, pady=4, padx=5)
        
        tk.Label(frame_form, text="Género:").grid(row=1, column=0, sticky="w", pady=4)
        self.combo_genero = ttk.Combobox(frame_form, values=["Masculino", "Femenino", "Otro"], state="readonly", width=32)
        self.combo_genero.grid(row=1, column=1, pady=4, padx=5)
        
        tk.Label(frame_form, text="Rol Asignado:").grid(row=2, column=0, sticky="w", pady=4)
        self.combo_rol = ttk.Combobox(frame_form, state="readonly", width=32)
        self.combo_rol.grid(row=2, column=1, pady=4, padx=5)
        
        frame_bio = tk.LabelFrame(self, text=" Carga Biométrica de Imágenes (Multiselección masiva) ", padx=10, pady=10)
        frame_bio.pack(fill="x", padx=15, pady=5)
        
        # Para seleccionar múltiples imágenes de una sola vez podés usar Ctrl o Shift dentro del explorador nativo.
        tk.Button(frame_bio, text="Añadir Fotos...", bg="#4B5563", fg="white", command=self.cargar_imagenes_locales).pack(side="left", padx=5)
        self.lbl_contador_imagenes = tk.Label(frame_bio, text="0 imágenes añadidas.", font=("Arial", 9, "italic"))
        self.lbl_contador_imagenes.pack(side="left", padx=10)

        frame_turno = tk.LabelFrame(self, text=" Configuración de Turnos y Descansos Variables ", padx=10, pady=10)
        frame_turno.pack(fill="x", padx=15, pady=5)
        
        grid_turno = tk.Frame(frame_turno)
        grid_turno.pack(fill="x")
        
        tk.Label(grid_turno, text="Día:").grid(row=0, column=0, sticky="w")
        self.combo_dia = ttk.Combobox(grid_turno, values=["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"], state="readonly", width=9)
        self.combo_dia.grid(row=0, column=1, padx=2)
        
        tk.Label(grid_turno, text="Turno:").grid(row=0, column=2, padx=2)
        self.entry_entrada = tk.Entry(grid_turno, width=5)
        self.entry_entrada.insert(0, "08:00")
        self.entry_entrada.grid(row=0, column=3)
        self.entry_salida = tk.Entry(grid_turno, width=5)
        self.entry_salida.insert(0, "17:00")
        self.entry_salida.grid(row=0, column=4)
        
        tk.Label(grid_turno, text="Descanso:").grid(row=0, column=5, padx=2)
        self.entry_desc_in = tk.Entry(grid_turno, width=5)
        self.entry_desc_in.insert(0, "12:00")
        self.entry_desc_in.grid(row=0, column=6)
        self.entry_desc_out = tk.Entry(grid_turno, width=5)
        self.entry_desc_out.insert(0, "13:00")
        self.entry_desc_out.grid(row=0, column=7)
        
        tk.Button(grid_turno, text="+", bg="#3B82F6", fg="white", command=self.agregar_turno_a_lista, width=2).grid(row=0, column=8, padx=4)
        
        self.tabla_turnos_temp = ttk.Treeview(frame_turno, columns=("Dia", "Horario", "Descanso"), show="headings", height=3)
        self.tabla_turnos_temp.heading("Dia", text="Día")
        self.tabla_turnos_temp.heading("Horario", text="Horario")
        self.tabla_turnos_temp.heading("Descanso", text="Descanso")
        self.tabla_turnos_temp.column("Dia", width=80)
        self.tabla_turnos_temp.column("Horario", width=160)
        self.tabla_turnos_temp.column("Descanso", width=160)
        self.tabla_turnos_temp.pack(fill="x", pady=5)

        tk.Button(self, text="GUARDAR EMPLEADO COMPLETO", bg="#10B981", fg="white", font=("Arial", 11, "bold"), height=2, command=self.procesar_guardado).pack(fill="x", padx=15, pady=10)
        tk.Button(self, text="ABRIR PANEL DE MONITOREO Y EDICIÓN", bg="#1E293B", fg="white", command=self.abrir_visualizacion).pack(fill="x", padx=15)

    def cargar_roles_combobox(self):
        try:
            conexion = obtener_conexion()
            cursor = conexion.cursor()
            cursor.execute("SELECT id, nombreRol FROM rol_empleado;")
            self.roles_db = cursor.fetchall()
            conexion.close()
            valores = [f"{r['id']} - {r['nombreRol']}" for r in self.roles_db]
            self.combo_rol['values'] = valores
            if valores: self.combo_rol.current(0)
        except Exception as e:
            print(e)

    def cargar_imagenes_locales(self):
        archivos = filedialog.askopenfilenames(title="Seleccionar imágenes", filetypes=[("Imágenes", "*.jpg *.jpeg *.png")])
        if archivos:
            # .extend acumula en lugar de pisar la selección previa
            self.imagenes_seleccionadas.extend(list(archivos))
            self.lbl_contador_imagenes.config(text=f"{len(self.imagenes_seleccionadas)} imágenes añadidas.")

    def agregar_turno_a_lista(self):
        dia = self.combo_dia.get()
        ent = self.entry_entrada.get().strip()
        sal = self.entry_salida.get().strip()
        din = self.entry_desc_in.get().strip()
        dout = self.entry_desc_out.get().strip()
        
        if not dia: return
        dias_map = {"Lunes": 1, "Martes": 2, "Miércoles": 3, "Jueves": 4, "Viernes": 5, "Sábado": 6, "Domingo": 7}
        self.turnos_temporales.append((dias_map[dia], ent, sal, din, dout))
        self.tabla_turnos_temp.insert("", "end", values=(dia, f"{ent} a {sal}", f"{din} a {dout}"))

    def procesar_guardado(self):
        nombre = self.entry_nombre.get().strip()
        genero = self.combo_genero.get()
        rol_sel = self.combo_rol.get()
        
        if not nombre or not genero or not rol_sel:
            messagebox.showerror("Error", "Faltan datos básicos.")
            return
            
        rol_id = int(rol_sel.split(" - ")[0])
        exito, msg = EmpleadoModel.crear_empleado(nombre, genero, 100.0, "Activo", rol_id, self.imagenes_seleccionadas, self.usuario_id)
        
        if exito:
            id_nuevo = EmpleadoModel.buscar_empleados(nombre)[0]['id']
            for d_id, ent, sal, din, dout in self.turnos_temporales:
                TurnoModel.asignar_turno_completo(id_nuevo, ent, sal, din, dout, [d_id], self.usuario_id)
            messagebox.showinfo("Éxito", "Empleado registrado.")
            self.limpiar_formulario()
        else:
            messagebox.showerror("Error", msg)

    def limpiar_formulario(self):
        self.entry_nombre.delete(0, tk.END)
        self.imagenes_seleccionadas = []
        self.turnos_temporales = []
        self.lbl_contador_imagenes.config(text="0 imágenes añadidas.")
        for item in self.tabla_turnos_temp.get_children(): self.tabla_turnos_temp.delete(item)

    def abrir_visualizacion(self):
        from views.visualizacion_view import VentanaVisualizacionExtra
        VentanaVisualizacionExtra(self, self.usuario_id)