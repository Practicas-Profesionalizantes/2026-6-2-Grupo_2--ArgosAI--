# main.py
from database.connection import inicializar_todo
from views import VentanaLogin, VentanaGestion

def lanzar_aplicacion_principal(usuario_id, usuario_nombre):
    """Crea una instancia limpia de la ventana principal sin ventanas fantasma."""
    app_sistema = VentanaGestion(usuario_id, usuario_nombre)
    app_sistema.mainloop()

if __name__ == "__main__":
    # Inicializa las tablas SQLite y la data semilla (usuarios, roles, días)
    inicializar_todo()
    
    # Lanza el login en su propia raíz Tk
    login = VentanaLogin(db_path="argosai.db", on_success=lanzar_aplicacion_principal)
    login.iniciar()