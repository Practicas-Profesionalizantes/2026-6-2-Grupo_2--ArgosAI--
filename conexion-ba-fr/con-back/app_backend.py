# con-back/app_backend.py (Corriendo en Python 3.6.8)
from flask import Flask, request, jsonify
from flask_socketio import SocketIO

app = Flask(__name__)
# Evitamos problemas de CORS permitiendo que cualquier cliente se conecte
socketio = SocketIO(app, cors_allowed_origins="*")

# Evento para ver en consola si el frontend se conectó
@socketio.on('connect')
def al_conectar():
    print("\n[WS] ¡La interfaz de Streamlit se ha conectado por WebSocket!")

# Ruta HTTP POST que simula la llegada de un nuevo dato (ej. una IA detecta algo)
@app.route('/notificar-cambio', methods=['POST'])
def notificar_cambio():
    datos_recibidos = request.json
    print(f"\n[HTTP] Nuevo dato recibido en el backend: {datos_recibidos}")
    
    # ¡AQUÍ OCURRE LA MAGIA! Retransmite en tiempo real al frontend
    socketio.emit('actualizacion_servidor', datos_recibidos)
    
    return jsonify({"status": "Éxito", "mensaje": "Datos retransmitidos al front"}), 200

if __name__ == '__main__':
    print("Servidor Backend escuchando en http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000)
