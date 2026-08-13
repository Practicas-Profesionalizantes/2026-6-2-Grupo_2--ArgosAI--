-- SQLite
CREATE TABLE usuario(
id INTEGER PRIMARY KEY AUTOINCREMENT,
nombre TEXT,
email TEXT,
contrasenia TEXT,
telefono TEXT
);

CREATE TABLE camara(
id INTEGER PRIMARY KEY AUTOINCREMENT,
ubicacion TEXT,
estado TEXT,
direccionIP TEXT
);

CREATE TABLE video(
id INTEGER PRIMARY KEY AUTOINCREMENT,
ruta TEXT,
fecha TEXT,
duracion TEXT,
tamanoArchivo REAL,
tiempoLimite TEXT,
camara_id INTEGER,
FOREIGN KEY (camara_id) REFERENCES camara(id)
);

CREATE TABLE rol_empleado(
id INTEGER PRIMARY KEY AUTOINCREMENT,
nombreRol TEXT,
descripcion TEXT
);

CREATE TABLE empleado(
id INTEGER PRIMARY KEY AUTOINCREMENT,
nombre TEXT,
genero TEXT,
rendimiento REAL,
estado TEXT,
urlImagen TEXT,
rol_id INTEGER,
FOREIGN KEY (rol_id) REFERENCES rol_empleado(id)
);

CREATE TABLE diasSemana(
id INTEGER PRIMARY KEY AUTOINCREMENT,
dia TEXT
);

CREATE TABLE turno(
id INTEGER PRIMARY KEY AUTOINCREMENT,
HoraInicio TEXT,
HoraFin TEXT,
empleado_id INTEGER,
FOREIGN KEY (empleado_id) REFERENCES empleado(id)
);

CREATE TABLE diasTurno(
id INTEGER PRIMARY KEY AUTOINCREMENT,
turno_id INTEGER,
diaSemana_id INTEGER,
FOREIGN KEY (turno_id) REFERENCES turno(id),
FOREIGN KEY (diaSemana_id) REFERENCES diasSemana(id)
);

CREATE TABLE horas(
id INTEGER PRIMARY KEY AUTOINCREMENT,
fechaYHoraEntrada TEXT,
fechaYHoraSalida TEXT,
empleado_id INTEGER,
FOREIGN KEY (empleado_id) REFERENCES empleado(id)
);

CREATE TABLE horas_extra(
id INTEGER PRIMARY KEY AUTOINCREMENT,
cantidad REAL,
horas_id INTEGER,
FOREIGN KEY (horas_id) REFERENCES horas(id)
);

CREATE TABLE actividad(
id INTEGER PRIMARY KEY AUTOINCREMENT,
tipoActividad TEXT,
fechaYHoraComienzo TEXT,
fechaYHoraFin TEXT,
empleado_id INTEGER,
FOREIGN KEY (empleado_id) REFERENCES empleado(id)
);

CREATE TABLE metrica(
id INTEGER PRIMARY KEY AUTOINCREMENT,
tipo TEXT
);

CREATE TABLE inforMetrica(
id INTEGER PRIMARY KEY AUTOINCREMENT,
actividad_id INTEGER,
metrica_id INTEGER,
FOREIGN KEY (actividad_id) REFERENCES actividad(id),
FOREIGN KEY (metrica_id) REFERENCES metrica(id)
);

CREATE TABLE alerta(
id INTEGER PRIMARY KEY AUTOINCREMENT,
grado TEXT,
incumplimiento TEXT,
fechaYHora TEXT,
empleado_id INTEGER,
FOREIGN KEY (empleado_id) REFERENCES empleado(id)
);

CREATE TABLE highlights(
id INTEGER PRIMARY KEY AUTOINCREMENT,
minutoInicio TEXT,
minutoFin TEXT,
video_id INTEGER,
actividad_id INTEGER,
FOREIGN KEY (video_id) REFERENCES video(id),
FOREIGN KEY (actividad_id) REFERENCES actividad(id)
);

CREATE TABLE revision_alerta(
id INTEGER PRIMARY KEY AUTOINCREMENT,
estadoRevision TEXT,
comentarios TEXT,
fechaYHoraRevision TEXT,
usuario_id INTEGER,
alerta_id INTEGER,
FOREIGN KEY (usuario_id) REFERENCES usuario(id),
FOREIGN KEY (alerta_id) REFERENCES alerta(id)
);

CREATE TABLE mov_sospechoso(
id INTEGER PRIMARY KEY AUTOINCREMENT,
minutoInicio TEXT,
minutoFin TEXT,
descripcionPersonaInvolucrada TEXT,
boundingBox TEXT,
video_id INTEGER,
FOREIGN KEY (video_id) REFERENCES video(id)
);

CREATE TABLE auditoria(
id INTEGER PRIMARY KEY AUTOINCREMENT,
accion TEXT,
usuario_id INTEGER,
tablaM TEXT,
registro_afectado_id INTEGER,
fecha TEXT,
FOREIGN KEY (usuario_id) REFERENCES usuario(id)
);

/* Triggers de inserts */
CREATE TRIGGER trg_after_insert_rolEmpleado
AFTER INSERT ON rol_empleado
FOR EACH ROW
BEGIN
INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
VALUES ('INSERT', NULL, 'rol_empleado', NEW.id, CURRENT_TIMESTAMP);
END;

CREATE TRIGGER trg_after_insert_empleado
AFTER INSERT ON empleado
FOR EACH ROW
BEGIN
INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
VALUES ('INSERT', NULL, 'empleado', NEW.id, CURRENT_TIMESTAMP);
END;

CREATE TRIGGER trg_after_insert_turno
AFTER INSERT ON turno
FOR EACH ROW
BEGIN
INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
VALUES ('INSERT', NULL, 'turno', NEW.id, CURRENT_TIMESTAMP);
END;

CREATE TRIGGER trg_after_insert_horas
AFTER INSERT ON horas
FOR EACH ROW
BEGIN
INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
VALUES ('INSERT', NULL, 'horas', NEW.id, CURRENT_TIMESTAMP);
END;

CREATE TRIGGER trg_after_insert_horasExtra
AFTER INSERT ON horas_extra
FOR EACH ROW
BEGIN
INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
VALUES ('INSERT', NULL, 'horas_extra', NEW.id, CURRENT_TIMESTAMP);
END;

CREATE TRIGGER trg_after_insert_actividad
AFTER INSERT ON actividad
FOR EACH ROW
BEGIN
INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
VALUES ('INSERT', NULL, 'actividad', NEW.id, CURRENT_TIMESTAMP);
END;

CREATE TRIGGER trg_after_insert_metrica
AFTER INSERT ON metrica
FOR EACH ROW
BEGIN
INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
VALUES ('INSERT', NULL, 'metrica', NEW.id, CURRENT_TIMESTAMP);
END;

CREATE TRIGGER trg_after_insert_alerta
AFTER INSERT ON alerta
FOR EACH ROW
BEGIN
INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
VALUES ('INSERT', NULL, 'alerta', NEW.id, CURRENT_TIMESTAMP);
END;

CREATE TRIGGER trg_after_insert_camara
AFTER INSERT ON camara
FOR EACH ROW
BEGIN
INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
VALUES ('INSERT', NULL, 'camara', NEW.id, CURRENT_TIMESTAMP);
END;

CREATE TRIGGER trg_after_insert_video
AFTER INSERT ON video
FOR EACH ROW
BEGIN
INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
VALUES ('INSERT', NULL, 'video', NEW.id, CURRENT_TIMESTAMP);
END;

CREATE TRIGGER trg_after_insert_highlights
AFTER INSERT ON highlights
FOR EACH ROW
BEGIN
INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
VALUES ('INSERT', NULL, 'highlights', NEW.id, CURRENT_TIMESTAMP);
END;

CREATE TRIGGER trg_after_insert_movSospechoso
AFTER INSERT ON mov_sospechoso
FOR EACH ROW
BEGIN
INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
VALUES ('INSERT', NULL, 'mov_sospechoso', NEW.id, CURRENT_TIMESTAMP);
END;

CREATE TRIGGER trg_after_insert_revisionAlerta
AFTER INSERT ON revision_alerta
FOR EACH ROW
BEGIN
INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
VALUES ('INSERT', NULL, 'revision_alerta', NEW.id, CURRENT_TIMESTAMP);
END;

CREATE TRIGGER trg_after_insert_usuario
AFTER INSERT ON usuario
FOR EACH ROW
BEGIN
INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
VALUES ('INSERT', NULL, 'usuario', NEW.id, CURRENT_TIMESTAMP);
END;

/* Triggers de update */
CREATE TRIGGER trg_after_update_rolEmpleado
AFTER UPDATE ON rol_empleado
FOR EACH ROW
BEGIN
INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
VALUES ('UPDATE', NULL, 'rol_empleado', NEW.id, CURRENT_TIMESTAMP);
END;

CREATE TRIGGER trg_after_update_empleado
AFTER UPDATE ON empleado
FOR EACH ROW
BEGIN
INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
VALUES ('UPDATE', NULL, 'empleado', NEW.id, CURRENT_TIMESTAMP);
END;

CREATE TRIGGER trg_after_update_turno
AFTER UPDATE ON turno
FOR EACH ROW
BEGIN
INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
VALUES ('UPDATE', NULL, 'turno', NEW.id, CURRENT_TIMESTAMP);
END;

CREATE TRIGGER trg_after_update_horas
AFTER UPDATE ON horas
FOR EACH ROW
BEGIN
INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
VALUES ('UPDATE', NULL, 'horas', NEW.id, CURRENT_TIMESTAMP);
END;

CREATE TRIGGER trg_after_update_horasExtra
AFTER UPDATE ON horas_extra
FOR EACH ROW
BEGIN
INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
VALUES ('UPDATE', NULL, 'horas_extra', NEW.id, CURRENT_TIMESTAMP);
END;

CREATE TRIGGER trg_after_update_actividad
AFTER UPDATE ON actividad
FOR EACH ROW
BEGIN
INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
VALUES ('UPDATE', NULL, 'actividad', NEW.id, CURRENT_TIMESTAMP);
END;

CREATE TRIGGER trg_after_update_metrica
AFTER UPDATE ON metrica
FOR EACH ROW
BEGIN
INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
VALUES ('UPDATE', NULL, 'metrica', NEW.id, CURRENT_TIMESTAMP);
END;

CREATE TRIGGER trg_after_update_alerta
AFTER UPDATE ON alerta
FOR EACH ROW
BEGIN
INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
VALUES ('UPDATE', NULL, 'alerta', NEW.id, CURRENT_TIMESTAMP);
END;

CREATE TRIGGER trg_after_update_camara
AFTER UPDATE ON camara
FOR EACH ROW
BEGIN
INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
VALUES ('UPDATE', NULL, 'camara', NEW.id, CURRENT_TIMESTAMP);
END;

CREATE TRIGGER trg_after_update_video
AFTER UPDATE ON video
FOR EACH ROW
BEGIN
INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
VALUES ('UPDATE', NULL, 'video', NEW.id, CURRENT_TIMESTAMP);
END;

CREATE TRIGGER trg_after_update_highlights
AFTER UPDATE ON highlights
FOR EACH ROW
BEGIN
INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
VALUES ('UPDATE', NULL, 'highlights', NEW.id, CURRENT_TIMESTAMP);
END;

CREATE TRIGGER trg_after_update_movSospechoso
AFTER UPDATE ON mov_sospechoso
FOR EACH ROW
BEGIN
INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
VALUES ('UPDATE', NULL, 'mov_sospechoso', NEW.id, CURRENT_TIMESTAMP);
END;

CREATE TRIGGER trg_after_update_revisionAlerta
AFTER UPDATE ON revision_alerta
FOR EACH ROW
BEGIN
INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
VALUES ('UPDATE', NULL, 'revision_alerta', NEW.id, CURRENT_TIMESTAMP);
END;

CREATE TRIGGER trg_after_update_usuario
AFTER UPDATE ON usuario
FOR EACH ROW
BEGIN
INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
VALUES ('UPDATE', NULL, 'usuario', NEW.id, CURRENT_TIMESTAMP);
END;

/* Triggers Delete */
CREATE TRIGGER trg_after_delete_rolEmpleado
AFTER DELETE ON rol_empleado
FOR EACH ROW
BEGIN
INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
VALUES ('DELETE', NULL, 'rol_empleado', OLD.id, CURRENT_TIMESTAMP);
END;

CREATE TRIGGER trg_after_delete_empleado
AFTER DELETE ON empleado
FOR EACH ROW
BEGIN
INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
VALUES ('DELETE', NULL, 'empleado', OLD.id, CURRENT_TIMESTAMP);
END;

CREATE TRIGGER trg_after_delete_turno
AFTER DELETE ON turno
FOR EACH ROW
BEGIN
INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
VALUES ('DELETE', NULL, 'turno', OLD.id, CURRENT_TIMESTAMP);
END;

CREATE TRIGGER trg_after_delete_horas
AFTER DELETE ON horas
FOR EACH ROW
BEGIN
INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
VALUES ('DELETE', NULL, 'horas', OLD.id, CURRENT_TIMESTAMP);
END;

CREATE TRIGGER trg_after_delete_horasExtra
AFTER DELETE ON horas_extra
FOR EACH ROW
BEGIN
INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
VALUES ('DELETE', NULL, 'horas_extra', OLD.id, CURRENT_TIMESTAMP);
END;

CREATE TRIGGER trg_after_delete_actividad
AFTER DELETE ON actividad
FOR EACH ROW
BEGIN
INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
VALUES ('DELETE', NULL, 'actividad', OLD.id, CURRENT_TIMESTAMP);
END;

CREATE TRIGGER trg_after_delete_metrica
AFTER DELETE ON metrica
FOR EACH ROW
BEGIN
INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
VALUES ('DELETE', NULL, 'metrica', OLD.id, CURRENT_TIMESTAMP);
END;

CREATE TRIGGER trg_after_delete_alerta
AFTER DELETE ON alerta
FOR EACH ROW
BEGIN
INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
VALUES ('DELETE', NULL, 'alerta', OLD.id, CURRENT_TIMESTAMP);
END;

CREATE TRIGGER trg_after_delete_camara
AFTER DELETE ON camara
FOR EACH ROW
BEGIN
INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
VALUES ('DELETE', NULL, 'camara', OLD.id, CURRENT_TIMESTAMP);
END;

CREATE TRIGGER trg_after_delete_video
AFTER DELETE ON video
FOR EACH ROW
BEGIN
INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
VALUES ('DELETE', NULL, 'video', OLD.id, CURRENT_TIMESTAMP);
END;

CREATE TRIGGER trg_after_delete_highlights
AFTER DELETE ON highlights
FOR EACH ROW
BEGIN
INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
VALUES ('DELETE', NULL, 'highlights', OLD.id, CURRENT_TIMESTAMP);
END;

CREATE TRIGGER trg_after_delete_movSospechoso
AFTER DELETE ON mov_sospechoso
FOR EACH ROW
BEGIN
INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
VALUES ('DELETE', NULL, 'mov_sospechoso', OLD.id, CURRENT_TIMESTAMP);
END;

CREATE TRIGGER trg_after_delete_revisionAlerta
AFTER DELETE ON revision_alerta
FOR EACH ROW
BEGIN
INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
VALUES ('DELETE', NULL, 'revision_alerta', OLD.id, CURRENT_TIMESTAMP);
END;

CREATE TRIGGER trg_after_delete_usuario
AFTER DELETE ON usuario
FOR EACH ROW
BEGIN
INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
VALUES ('DELETE', NULL, 'usuario', OLD.id, CURRENT_TIMESTAMP);
END;
PRAGMA journal_mode=WAL;
