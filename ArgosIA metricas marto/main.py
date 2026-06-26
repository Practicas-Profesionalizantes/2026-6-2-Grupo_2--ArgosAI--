import sys
import os
import tkinter as tk

# Esto agrega la ruta actual a Python para que encuentre las carpetas
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Así es como le decís a Python: 
# "Dentro de la carpeta models, en el archivo vista_rendimiento, busca la clase AppARGOSAI"
from models.vista_rendimiento import AppARGOSAI

if __name__ == "__main__":
    root = tk.Tk()
    # Cambié el nombre de la clase a AppARGOSAI para que tenga sentido
    app = AppARGOSAI(root)
    root.mainloop()