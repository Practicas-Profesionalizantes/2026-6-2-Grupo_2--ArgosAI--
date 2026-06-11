import tkinter as tk
from tkinter import messagebox
import hashlib
import sqlite3

DATABASE_FILE = "argosai.db"

def calcular_hash_sha256(texto):
    return hashlib.sha256(texto.encode('utf-8')).hexdigest()

def ejecutar_login():
    email = entry_email.get().strip()
    contrasenia = entry_password.get().strip()

    if not email or not contrasenia:
        messagebox.showwarning("Campos incompletos", "Por favor, ingrese tanto el email como la contraseña.")
        return

    try:
        # Conexión directa al archivo local
        conexion = sqlite3.connect(DATABASE_FILE)
        # Configuramos el row_factory para interactuar mediante nombres de columnas
        conexion.row_factory = sqlite3.Row
        cursor = conexion.cursor()

        # Al no haber procedimiento almacenado, la lógica se procesa en esta Query lineal
        query = "SELECT id, nombre, contrasenia FROM usuario WHERE email = ?"
        cursor.execute(query, (email,))
        usuario = cursor.fetchone()

        if usuario:
            hash_ingresado = calcular_hash_sha256(contrasenia)

            if usuario['contrasenia'] == hash_ingresado:
                user_nombre = usuario['nombre']
                
                # Desafío de diseño: Para implementar la auditoría aquí, 
                # tendríamos que hacer un INSERT explícito en una tabla de auditoría 
                # desde este preciso bloque de código, ya que no hay @current_user_id.
                
                messagebox.showinfo("Acceso Concedido", f"Bienvenido, {user_nombre}.\nSesión iniciada localmente.")
                root.destroy()
            else:
                messagebox.showerror("Error de Autenticación", "La contraseña ingresada es incorrecta.")
        else:
            messagebox.showerror("Error de Autenticación", "El correo electrónico no se encuentra registrado.")

    except sqlite3.Error as e:
        messagebox.showerror("Error de Base de Datos", f"Fallo al operar en el archivo DB:\n{e}")
    finally:
        if conexion:
            conexion.close()

# --- INTERFAZ GRÁFICA ---
root = tk.Tk()
root.title("ARGOSAI - Login Local")
root.geometry("380x280")
root.resizable(False, False)

frame_principal = tk.Frame(root)
frame_principal.pack(expand=True, fill="both", padx=40, pady=25)

lbl_titulo = tk.Label(frame_principal, text="ARGOS AI (Local)", font=("Arial", 16, "bold"), fg="#1E293B")
lbl_titulo.pack(pady=(0, 15))

lbl_email = tk.Label(frame_principal, text="Correo Electrónico:", font=("Arial", 10))
lbl_email.pack(anchor="w")
entry_email = tk.Entry(frame_principal, font=("Arial", 11), width=30)
entry_email.pack(pady=(2, 10))
entry_email.focus()

lbl_password = tk.Label(frame_principal, text="Contraseña:", font=("Arial", 10))
lbl_password.pack(anchor="w")
entry_password = tk.Entry(frame_principal, font=("Arial", 11), width=30, show="*")
entry_password.pack(pady=(2, 20))

btn_login = tk.Button(
    frame_principal, 
    text="Iniciar Sesión", 
    font=("Arial", 11, "bold"), 
    bg="#10B981", # Verde para diferenciar la versión local
    fg="white", 
    activebackground="#059669", 
    activeforeground="white",
    width=18,
    command=ejecutar_login,
    cursor="hand2"
)
btn_login.pack(pady=5)

root.bind('<Return>', lambda event: ejecutar_login())

# Asegurar que el archivo exista antes de lanzar la interfaz
try:
    inicializar_conexion = sqlite3.connect(DATABASE_FILE)
    inicializar_conexion.close()
except:
    pass

root.mainloop()