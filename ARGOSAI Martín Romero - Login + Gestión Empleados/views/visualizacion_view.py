# views/visualizacion_view.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from PIL import Image, ImageTk
from models.empleado_model import EmpleadoModel
from models.turno_model import TurnoModel
from models.horas_model import HorasModel
from models import EmpleadoModel, TurnoModel, HorasModel
from database.connection import obtener_conexion

class VentanaVisualizacionExtra(tk.Toplevel):
    def __init__(self, parent, usuario_id):
        super().__init__(parent)
        self.usuario_id = usuario_id
        self.title("ARGOSAI - Panel de Control, Edición y Monitoreo")
        self.geometry("900(x)680") if False else self.geometry("920x720")
        
        self.ruta_carpeta_actual = ""
        self.id_empleado_seleccionado = None
        self.id_turno_seleccionado = None
        
        # --- Buscador ---
        frame_busqueda = tk.Frame(self, pady=5)
        frame_busqueda.pack(fill="x", padx=10, pady=2)
        tk.Label(frame_busqueda, text="Filtrar por Nombre:").pack(side="left", padx=5)
        self.entry_busqueda = tk.Entry(frame_busqueda, width=25)
        self.entry_busqueda.pack(side="left", padx=5)
        tk.Button(frame_busqueda, text="Buscar", bg="#3B82F6", fg="white", command=self.cargar_empleados_tabla).pack(side="left", padx=5)
        tk.Button(frame_busqueda, text="Eliminar Empleado", bg="#EF4444", fg="white", command=self.eliminar_empleado_tabla).pack(side="right", padx=5)
        
        # --- Tabla Maestra ---
        self.tabla = ttk.Treeview(self, columns=("ID", "Nombre", "Género", "Rol", "Estado"), show="headings", height=5)
        self.tabla.heading("ID", text="ID")
        self.tabla.heading("Nombre", text="Nombre")
        self.tabla.heading("Género", text="Género")
        self.tabla.heading("Rol", text="Rol (Puesto)")
        self.tabla.heading("Estado", text="Estado")
        self.tabla.column("ID", width=40, anchor="center")
        self.tabla.pack(fill="x", padx=10, pady=5)
        self.tabla.bind("<<TreeviewSelect>>", self.al_seleccionar_empleado)
        
        # --- FORMULARIO DE MODIFICACIÓN DE DATOS (EDICIÓN DIRECTA) ---
        frame_edicion = tk.LabelFrame(self, text=" Modificar Datos del Empleado Seleccionado ", padx=10, pady=5)
        frame_edicion.pack(fill="x", padx=10, pady=5)
        
        tk.Label(frame_edicion, text="Nombre:").grid(row=0, column=0, padx=2, pady=2, sticky="w")
        self.edit_nombre = tk.Entry(frame_edicion, width=20)
        self.edit_nombre.grid(row=0, column=1, padx=4, pady=2)
        
        tk.Label(frame_edicion, text="Género:").grid(row=0, column=2, padx=2, pady=2, sticky="w")
        self.edit_genero = ttk.Combobox(frame_edicion, values=["Masculino", "Femenino", "Otro"], state="readonly", width=12)
        self.edit_genero.grid(row=0, column=3, padx=4, pady=2)
        
        tk.Label(frame_edicion, text="Rol:").grid(row=0, column=4, padx=2, pady=2, sticky="w")
        self.edit_rol = ttk.Combobox(frame_edicion, state="readonly", width=15)
        self.edit_rol.grid(row=0, column=5, padx=4, pady=2)
        
        tk.Label(frame_edicion, text="Estado:").grid(row=0, column=6, padx=2, pady=2, sticky="w")
        self.edit_estado = ttk.Combobox(frame_edicion, values=["Activo", "Inactivo", "Licencia"], state="readonly", width=10)
        self.edit_estado.grid(row=0, column=7, padx=4, pady=2)
        
        tk.Button(frame_edicion, text="Guardar Cambios", bg="#10B981", fg="white", font=("Arial", 9, "bold"), command=self.ejecutar_modificacion_empleado).grid(row=0, column=8, padx=10, pady=2)

        # --- Notebook de Detalles ---
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.tab_biometria = tk.Frame(self.notebook)
        self.tab_turnos = tk.Frame(self.notebook)
        self.tab_horas_extra = tk.Frame(self.notebook)
        
        self.notebook.add(self.tab_biometria, text=" Muestras de Rostros (IA) ")
        self.notebook.add(self.tab_turnos, text=" Turnos y Descansos ")
        self.notebook.add(self.tab_horas_extra, text=" Historial de Horas Extra ")
        
        # --- SUBDISEÑO PESTAÑA BIOMETRÍA ---
        frame_list_bio = tk.Frame(self.tab_biometria)
        frame_list_bio.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        self.listbox_fotos = tk.Listbox(frame_list_bio, height=6)
        self.listbox_fotos.pack(fill="both", expand=True, pady=2)
        self.listbox_fotos.bind("<<ListboxSelect>>", self.al_seleccionar_foto_individual)
        
        btn_panel_bio = tk.Frame(frame_list_bio)
        btn_panel_bio.pack(fill="x")
        tk.Button(btn_panel_bio, text="Añadir Fotos Extra", bg="#3B82F6", fg="white", command=self.inyectar_fotos_en_caliente).pack(side="left", fill="x", expand=True, padx=2)
        tk.Button(btn_panel_bio, text="Borrar Seleccionada", bg="#F59E0B", fg="white", command=self.borrar_foto_individual).pack(side="right", fill="x", expand=True, padx=2)
        
        self.frame_visor = tk.LabelFrame(self.tab_biometria, text=" Visor de Imagen Real ", width=180, height=180)
        self.frame_visor.pack(side="right", padx=15, pady=5)
        self.frame_visor.pack_propagate(False)
        self.lbl_render_foto = tk.Label(self.frame_visor, text="Sin foto")
        self.lbl_render_foto.pack(expand=True, fill="both")
        
        # --- SUBDISEÑO PESTAÑA TURNOS (AHORA EDITABLE) ---
        self.tabla_t = ttk.Treeview(self.tab_turnos, columns=("ID", "Dias", "Entrada", "Salida", "DescIn", "DescOut"), show="headings", height=4)
        self.tabla_t.heading("ID", text="ID Turno")
        self.tabla_t.heading("Dias", text="Días")
        self.tabla_t.heading("Entrada", text="Entrada")
        self.tabla_t.heading("Salida", text="Salida")
        self.tabla_t.heading("DescIn", text="Descanso Inicio")
        self.tabla_t.heading("DescOut", text="Descanso Fin")
        self.tabla_t.column("ID", width=60, anchor="center")
        self.tabla_t.pack(fill="x", padx=5, pady=5)
        self.tabla_t.bind("<<TreeviewSelect>>", self.al_seleccionar_turno_tabla)
        
        frame_edit_t = tk.Frame(self.tab_turnos)
        frame_edit_t.pack(fill="x", padx=5, pady=2)
        tk.Label(frame_edit_t, text="Entrada:").grid(row=0, column=0, padx=2)
        self.t_ent = tk.Entry(frame_edit_t, width=8)
        self.t_ent.grid(row=0, column=1, padx=2)
        tk.Label(frame_edit_t, text="Salida:").grid(row=0, column=2, padx=2)
        self.t_sal = tk.Entry(frame_edit_t, width=8)
        self.t_sal.grid(row=0, column=3, padx=2)
        tk.Label(frame_edit_t, text="Desc. Inicio:").grid(row=0, column=4, padx=2)
        self.t_din = tk.Entry(frame_edit_t, width=8)
        self.t_din.grid(row=0, column=5, padx=2)
        tk.Label(frame_edit_t, text="Desc. Fin:").grid(row=0, column=6, padx=2)
        self.t_dout = tk.Entry(frame_edit_t, width=8)
        self.t_dout.grid(row=0, column=7, padx=2)
        
        tk.Button(frame_edit_t, text="Modificar Horarios/Descanso", bg="#F59E0B", fg="white", command=self.ejecutar_modificacion_turno).grid(row=0, column=8, padx=10)

        # --- SUBDISEÑO HISTORIAL HORAS EXTRA ---
        self.tabla_he = ttk.Treeview(self.tab_horas_extra, columns=("Entrada", "Salida", "Cantidad"), show="headings")
        self.tabla_he.heading("Entrada", text="Entrada Fichada")
        self.tabla_he.heading("Salida", text="Salida Fichada")
        self.tabla_he.heading("Cantidad", text="Horas Extra")
        self.tabla_he.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.cargar_roles_edicion()
        self.cargar_empleados_tabla()

    def cargar_roles_edicion(self):
        try:
            conexion = obtener_conexion()
            cursor = conexion.cursor()
            cursor.execute("SELECT id, nombreRol FROM rol_empleado;")
            self.roles_lista = cursor.fetchall()
            conexion.close()
            self.edit_rol['values'] = [f"{r['id']} - {r['nombreRol']}" for r in self.roles_lista]
        except Exception as e: print(e)

    def cargar_empleados_tabla(self):
        for f in self.tabla.get_children(): self.tabla.delete(f)
        filtro = self.entry_busqueda.get().strip()
        for emp in EmpleadoModel.buscar_empleados(filtro):
            self.tabla.insert("", "end", values=(emp['id'], emp['nombre'], emp['genero'], emp['nombreRol'], emp['estado']))

    def al_seleccionar_empleado(self, event):
        item = self.tabla.selection()
        if not item: return
        valores = self.tabla.item(item)['values']
        self.id_empleado_seleccionado = valores[0]
        
        # Auto-populado del Formulario de Edición
        self.edit_nombre.delete(0, tk.END)
        self.edit_nombre.insert(0, valores[1])
        self.edit_genero.set(valores[2])
        self.edit_estado.set(valores[4])
        
        for r_val in self.edit_rol['values']:
            if valores[3] in r_val:
                self.edit_rol.set(r_val)
                break
                
        # Limpieza de pestañas hijas
        self.lbl_render_foto.config(image="", text="Seleccione archivo")
        self.listbox_fotos.delete(0, tk.END)
        for f in self.tabla_t.get_children(): self.tabla_t.delete(f)
        for f in self.tabla_he.get_children(): self.tabla_he.delete(f)
        
        # 1. Cargar Biometría
        empleados = EmpleadoModel.buscar_empleados()
        emp_sel = next(e for e in empleados if e['id'] == self.id_empleado_seleccionado)
        self.ruta_carpeta_actual = emp_sel['urlImagen']
        if self.ruta_carpeta_actual and os.path.exists(self.ruta_carpeta_actual):
            for archivo in os.listdir(self.ruta_carpeta_actual):
                if archivo.lower().endswith(('.png', '.jpg', '.jpeg')):
                    self.listbox_fotos.insert(tk.END, archivo)
                    
        # 2. Cargar Turnos con Descansos
        for t in TurnoModel.obtener_turnos_por_empleado(self.id_empleado_seleccionado):
            self.tabla_t.insert("", "end", values=(t['id'], t['dias'], t['HoraInicio'], t['HoraFin'], t['DescansoInicio'], t['DescansoFin']))
            
        # 3. Cargar Horas Extra (Acá va a figurar la data insertada para el id 2)
        for h in HorasModel.obtener_horas_extra_empleado(self.id_empleado_seleccionado):
            self.tabla_he.insert("", "end", values=(h['fechaYHoraEntrada'], h['fechaYHoraSalida'], f"{h['cantidad']} Hs"))

    def ejecutar_modificacion_empleado(self):
        if not self.id_empleado_seleccionado: return
        nom = self.edit_nombre.get().strip()
        gen = self.edit_genero.get()
        est = self.edit_estado.get()
        rol_id = int(self.edit_rol.get().split(" - ")[0])
        
        exito, msg = EmpleadoModel.actualizar_empleado(self.id_empleado_seleccionado, nom, gen, rol_id, est, self.usuario_id)
        if exito:
            messagebox.showinfo("Éxito", msg)
            self.cargar_empleados_tabla()
        else:
            messagebox.showerror("Error", msg)

    def inyectar_fotos_en_caliente(self):
        """Añade imágenes de forma incremental al empleado seleccionado sin pisar las anteriores."""
        if not self.id_empleado_seleccionado: return
        archivos = filedialog.askopenfilenames(title="Agregar fotos incrementales", filetypes=[("Imágenes", "*.jpg *.jpeg *.png")])
        if archivos:
            exito, msg = EmpleadoModel.agregar_fotos_existentes(self.id_empleado_seleccionado, list(archivos), self.usuario_id)
            messagebox.showinfo("Biometría Actualizada", msg)
            self.al_seleccionar_empleado(None)

    def al_seleccionar_turno_tabla(self, event):
        item = self.tabla_t.selection()
        if not item: return
        v = self.tabla_t.item(item)['values']
        self.id_turno_seleccionado = v[0]
        
        self.t_ent.delete(0, tk.END); self.t_ent.insert(0, v[2] if v[2] else "")
        self.t_sal.delete(0, tk.END); self.t_sal.insert(0, v[3] if v[3] else "")
        self.t_din.delete(0, tk.END); self.t_din.insert(0, v[4] if v[4] else "")
        self.t_dout.delete(0, tk.END); self.t_dout.insert(0, v[5] if v[5] else "")

    def ejecutar_modificacion_turno(self):
        if not self.id_turno_seleccionado:
            messagebox.showwarning("Selección vacía", "Elegí un turno de la lista inferior primero.")
            return
        exito, msg = TurnoModel.actualizar_horarios_turno(
            self.id_turno_seleccionado, 
            self.t_ent.get().strip(), 
            self.t_sal.get().strip(), 
            self.t_din.get().strip(), 
            self.t_dout.get().strip(), 
            self.usuario_id
        )
        if exito:
            messagebox.showinfo("Éxito", msg)
            self.al_seleccionar_empleado(None)

    def al_seleccionar_foto_individual(self, event):
        seleccion = self.listbox_fotos.curselection()
        if not seleccion: return
        r = os.path.join(self.ruta_carpeta_actual, self.listbox_fotos.get(seleccion[0]))
        try:
            img = Image.open(r).resize((160, 160), Image.Resampling.LANCZOS)
            self.foto_tk = ImageTk.PhotoImage(img)
            self.lbl_render_foto.config(image=self.foto_tk, text="")
        except:
            self.lbl_render_foto.config(image="", text="Error de visualización")

    def borrar_foto_individual(self):
        seleccion = self.listbox_fotos.curselection()
        if not seleccion or not messagebox.askyesno("Confirmar", "¿Borrar esta muestra?"): return
        os.remove(os.path.join(self.ruta_carpeta_actual, self.listbox_fotos.get(seleccion[0])))
        self.al_seleccionar_empleado(None)

    def eliminar_empleado_tabla(self):
        if not self.id_empleado_seleccionado or not messagebox.askyesno("Crítico", "¿Eliminar empleado completo?"): return
        EmpleadoModel.eliminar_empleado(self.id_empleado_seleccionado, self.usuario_id)
        self.cargar_empleados_tabla()