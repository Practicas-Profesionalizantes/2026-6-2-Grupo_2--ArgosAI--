# views/login_view.py
import tkinter as tk
from tkinter import messagebox
import hashlib
import sqlite3

class VentanaLogin:
    def __init__(self, db_path="argosai.db", on_success=None):
        self.db_path = db_path
        self.on_success = on_success  # Función que se ejecutará al loguearse con éxito
        
        self.root = tk.Tk()
        self.root.title("ARGOSAI - Login Local")
        self.root.geometry("380x280")
        self.root.resizable(False, False)
        
        self.crear_interfaz()
        
    def calcular_hash_sha256(self, texto):
        return hashlib.sha256(texto.encode('utf-8')).hexdigest()

    def ejecutar_login(self):
        email = self.entry_email.get().strip()
        contrasenia = self.entry_password.get().strip()

        if not email or not contrasenia:
            messagebox.showwarning("Campos incompletos", "Por favor, ingrese tanto el email como la contraseña.")
            return

        conexion = None
        try:
            conexion = sqlite3.connect(self.db_path)
            conexion.row_factory = sqlite3.Row
            cursor = conexion.cursor()

            query = "SELECT id, nombre, contrasenia FROM usuario WHERE email = ?"
            cursor.execute(query, (email,))
            usuario = cursor.fetchone()

            if usuario:
                hash_ingresado = self.calcular_hash_sha256(contrasenia)

                if usuario['contrasenia'] == hash_ingresado:
                    user_id = usuario['id']
                    user_nombre = usuario['nombre']
                    
                    messagebox.showinfo("Acceso Concedido", f"Bienvenido, {user_nombre}.")
                    
                    # Rompemos el loop del login y disolvemos la ventana
                    self.root.destroy()
                    
                    # Si definimos una función de éxito, le mandamos los datos de sesión
                    if self.on_success:
                        self.on_success(user_id, user_nombre)
                else:
                    messagebox.showerror("Error de Autenticación", "La contraseña ingresada es incorrecta.")
            else:
                messagebox.showerror("Error de Autenticación", "El correo electrónico no se encuentra registrado.")

        except sqlite3.Error as e:
            messagebox.showerror("Error de Base de Datos", f"Fallo al operar en el archivo DB:\n{e}")
        finally:
            if conexion:
                conexion.close()

    def crear_interfaz(self):
        frame_principal = tk.Frame(self.root)
        frame_principal.pack(expand=True, fill="both", padx=40, pady=25)

        lbl_titulo = tk.Label(frame_principal, text="ARGOS AI (Local)", font=("Arial", 16, "bold"), fg="#1E293B")
        lbl_titulo.pack(pady=(0, 15))

        lbl_email = tk.Label(frame_principal, text="Correo Electrónico:", font=("Arial", 10))
        lbl_email.pack(anchor="w")
        self.entry_email = tk.Entry(frame_principal, font=("Arial", 11), width=30)
        self.entry_email.pack(pady=(2, 10))
        self.entry_email.focus()

        lbl_password = tk.Label(frame_principal, text="Contraseña:", font=("Arial", 10))
        lbl_password.pack(anchor="w")
        self.entry_password = tk.Entry(frame_principal, font=("Arial", 11), width=30, show="*")
        self.entry_password.pack(pady=(2, 20))

        btn_login = tk.Button(
            frame_principal, 
            text="Iniciar Sesión", 
            font=("Arial", 11, "bold"), 
            bg="#10B981", 
            fg="white", 
            activebackground="#059669", 
            activeforeground="white",
            width=18,
            command=self.ejecutar_login,
            cursor="hand2"
        )
        btn_login.pack(pady=5)

        self.root.bind('<Return>', lambda event: self.ejecutar_login())

    def iniciar(self):
        self.root.mainloop()