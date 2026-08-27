# ArgosIA

# Descripción del Proyecto
   
ArgosIA es un sistema inteligente de monitoreo y optimización de productividad para heladerías basado en Edge AI (Inteligencia Artificial en el Borde). El sistema utiliza una cámara conectada a un hardware embebido (Orbitty carrier) que ejecuta localmente un modelo de visión artificial (YOLOv5) para verificar en tiempo real si el empleado está realizando sus tareas mediante el registro de movimientos clave.

Los eventos detectados son transmitidos automáticamente a un backend centralizado que almacena los registros de forma segura en una base de datos distribuida en la nube (Turso), permitiendo su visualización y control a través de un panel moderno.

# Funcionalidades
Captura de video en tiempo real: Recepción de fotogramas desde las áreas clave de la heladería (caja, atención, preparación).

Procesamiento local con IA: Detección de movimientos y validación de actividad laboral mediante YOLOv5 ejecutado en la placa de borde.

Comunicación asíncrona por eventos: Transmisión ligera de metadatos (estado, timestamp, ID de empleado) desde el Orbitty hacia el backend vía solicitudes HTTP.

Gestión y persistencia centralizada: Almacenamiento optimizado de registros de actividad en una base de datos SQLite distribuida (Turso).

Panel de visualización y reportes: Interfaz y consultas orientadas al análisis de desempeño y estadísticas operativas del personal.

# Acceso al Proyecto
   
Puedes clonar el repositorio y acceder a los distintos módulos del sistema utilizando los siguientes comandos en tu terminal:

# Clonar el repositorio
git clone https://github.com/tu-usuario/ArgosIA.git

# Acceder al directorio del proyecto
cd ArgosIA

Subsistema de Borde (Orbitty): Scripts de Python 3.6.8 con YOLOv5 y OpenCV para la captura e inferencia local.
Backend y Base de Sincronización: API construida en Python 3.13 con conexión integrada a Turso (libsql).

# Tecnologías Utilizadas

Inteligencia Artificial y Visión por Computador: YOLOv5, OpenCV, PyTorch (optimizado para entorno de borde).
Hardware Embebido: Placa NVIDIA Jetson con Orbitty carrier.

Backend y Procesamiento: Python 3.13, Python 3.6.8 (Edge), FastAPI / librerías de red (requests).

Base de Datos: Turso (libSQL / SQLite en la nube).

Control de Versiones y Gestión: Git y GitHub.

# Personas Contribuyentes
Agradecimientos especiales a la comunidad y colaboradores externos que apoyaron en las pruebas de campo y optimización del dataset.

# Personas Desarrolladoras del Proyecto
   
Martin Lopez Schillaci.

Rosendo Osores.

Martin Romero Caqui.

Gaston Amaya.

Thiago Casiano.

7. Licencia
Este proyecto se encuentra bajo la licencia MIT. Siéntase libre de utilizar, modificar y adaptar el código según las necesidades del negocio.


