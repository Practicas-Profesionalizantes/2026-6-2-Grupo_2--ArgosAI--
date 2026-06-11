CREATE DATABASE ARGOSAI;

USE ARGOSAI;

CREATE TABLE usuario(
	id int primary key,
	nombre varchar(50),
	email varchar(50),
	contrasenia varchar(255),
	telefono varchar(17)
);
CREATE TABLE camara(
	id int primary key,
	ubicacion varchar(50),
	estado varchar(50),
	direccionIP varchar(50)
);
CREATE TABLE video(
	id int primary key,
	ruta varchar(1000),
	fecha date,
	duracion time,
	tamanoArchivo float,
	tiempoLimite date, /* EstadoProcesamiento */ /* Cuando sea la fecha que marca se borra */
	camara_id int,
	foreign key (camara_id) REFERENCES camara(id) 
);
CREATE TABLE rol_empleado(
	id int primary key,
	nombreRol varchar(50),
	descripcion varchar(200)
);
CREATE TABLE empleado(
	id int primary key,
	nombre varchar(50),
	genero varchar(50),
	rendimiento float,
	estado varchar(50),
	urlImagen varchar(2000), /* MODIFICADO */
	/*vectorFacial varchar(1000)*/ /* averiguar cuanta cantidad */
	rol_id int,
	FOREIGN KEY (rol_id) REFERENCES rol_empleado(id)
);
CREATE TABLE diasSemana( /* TABLA NUEVA */
	id int primary key,
	dia varchar(50)
);
CREATE TABLE turno(
	id int primary key,
	HoraInicio time, /* MODIFICADO */
	HoraFin time, /* MODIFICADO */
	empleado_id int,
	foreign key (empleado_id) REFERENCES empleado(id)
);
CREATE TABLE diasTurno( /* TABLA NUEVA */
	id int primary key,
	turno_id int,
	diaSemana_id int,
	FOREIGN KEY (turno_id) REFERENCES turno(id),
	FOREIGN KEY (diasemana_id) REFERENCES diasSemana(id)
);
CREATE TABLE horas(
	id int primary key,
	fechaYHoraEntrada datetime,
	fechaYHoraSalida datetime,
	empleado_id int,
	foreign key (empleado_id) REFERENCES empleado(id)
);
CREATE TABLE horas_extra(
	id int primary key,
	cantidad float,
	horas_id int,
	foreign key (horas_id) REFERENCES horas(id)
);
CREATE TABLE actividad(
	id int primary key,
	tipoActividad varchar(100),
	fechaYHoraComienzo datetime,
	fechaYHoraFin datetime,
	empleado_id int,
	FOREIGN KEY (empleado_id) REFERENCES empleado(id)
);
CREATE TABLE metrica(
	id int primary key,
	tipo varchar(50)
);
CREATE TABLE inforMetrica( /* TABLA NUEVA */
	id int primary key,
	actividad_id int,
	metrica_id int,
	FOREIGN KEY (actividad_id) REFERENCES actividad(id),
	FOREIGN KEY (metrica_id) REFERENCES metrica(id)
);
CREATE TABLE alerta(
	id int primary key,
	grado varchar(50),
	incumplimiento varchar(100),
	fechaYHora datetime,
	empleado_id int,
	FOREIGN KEY (empleado_id) REFERENCES empleado(id)
);
CREATE TABLE highlights( /* MODIFICADO */
	id int primary key,
	minutoInicio time, /* NUEVO */
	minutoFin time, /* NUEVO */
	video_id int,
	actividad_id int,
	FOREIGN KEY (video_id) REFERENCES video(id),
	FOREIGN KEY (actividad_id) REFERENCES actividad(id)
);
CREATE TABLE revision_alerta(
	id int primary key,
	estadoRevision varchar(50),
	comentarios varchar(200),
	fechaYHoraRevision datetime,
	usuario_id int,
	alerta_id int,
	FOREIGN KEY (usuario_id) REFERENCES usuario(id),
	FOREIGN KEY (alerta_id) REFERENCES alerta(id)
);
CREATE TABLE mov_sospechoso(
	id int primary key,
	minutoInicio time, /* NUEVO */
	minutoFin time, /* NUEVO */
	descripcionPersonaInvolucrada varchar(500),
	boundingBox varchar(500), /* El cuadro con el que la IA detecta el movimiento. */
	video_id int, /* NUEVO */
	FOREIGN KEY (video_id) REFERENCES video(id) /* NUEVO */
);

CREATE TABLE auditoria(
	id int AUTO_INCREMENT PRIMARY KEY,
	accion varchar(50),
	usuario_id int,
	tablaM varchar(50),
	registro_afectado_id int,
	fecha datetime,
	foreign key (usuario_id) references usuario(id)
);


/* Pendiente generar inserts para los roles de los empleados y para los días de la semana*/

/* Delimiter de Stored Procedures */

DELIMITER // 
CREATE PROCEDURE cu(IN nombreN VARCHAR(50), IN emailN varchar(50), IN contraseniaN VARCHAR(50), IN telefonoN varchar(50), OUT mensaje varchar(50)) /* Crear Usuario */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	START TRANSACTION;
		INSERT INTO usuario(nombre, email, contrasenia, telefono)
		VALUES(nombreN, emailN, contraseniaN, telefonoN);
	COMMIT;
	SET mensaje = 'Usuario creado con éxito.';
 END //
 
CREATE PROCEDURE gc(IN ubicacionN VARCHAR(50), IN estadoN varchar(50), IN direccionIPN VARCHAR(50), OUT mensaje varchar(50)) /* Guardar Cámara */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	START TRANSACTION;
		INSERT INTO camara(ubicacion, estado, direccionIP)
		VALUES(ubicacionN, estadoN, direccionIPN);
	COMMIT;
	SET mensaje = 'Cámara guardada con éxito.';
 END //
 
CREATE PROCEDURE vtc(OUT mensaje varchar(50)) /* Ver todas las cámaras */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	SELECT * FROM camara;
	SET mensaje = 'Mostrando cámaras..';
 END //
 
CREATE PROCEDURE vdc(IN id_camara int, OUT mensaje varchar(50)) /* Ver datos de una cámara */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	SELECT * FROM camara WHERE id = id_camara;
	SET mensaje = CONCAT('Mostrando datos de la cámara con el id .', id_camara);
 END //
 
CREATE PROCEDURE bc(IN id_camara int, OUT mensaje varchar(50)) /* Borrar Cámara */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	START TRANSACTION;
		DELETE FROM camara WHERE id = id_camara;
	COMMIT;
	SET mensaje = 'Cámara borrada con éxito.';
 END //
 
 CREATE PROCEDURE mc(IN id_camara int, IN ubicacionN varchar(50), IN estadoN varchar(50), IN direccionIPN varchar(50), OUT mensaje varchar(50)) /* Modificar Cámara */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	START TRANSACTION;
		UPDATE camara 
		SET ubicacion = ubicacionN, estado = estadoN, direccionIP = direccionIPN
		WHERE id = id_camara;
	COMMIT;
	SET mensaje = 'Cámara modificada con éxito.';
 END //
 
CREATE PROCEDURE gv(IN rutaN varchar(1000), IN fechaN date, IN duracionN time, IN tamanoArchivoN float,IN estadoProcesamientoN varchar(50), IN camara_idN int,OUT mensaje varchar(50)) /* Guardar Video */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	START TRANSACTION;
		INSERT INTO video(ruta, fecha, duracion, tamanoArchivo, estadoProcesamiento, camara_id)
		VALUES(rutaN, fechaN, duracionN, tamanoArchivoN, estadoProcesamientoN, camara_idN);
	COMMIT;
	SET mensaje = 'Video guardado con éxito.';
 END //
 
CREATE PROCEDURE mv(OUT mensaje varchar(50)) /* Mostrar Videos */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	SELECT * FROM video;
	SET mensaje = 'Mostrando videos...';
 END //
 
CREATE PROCEDURE bv(IN id_video int, OUT mensaje varchar(50)) /* Borrar Video */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
    START TRANSACTION;
		DELETE FROM video WHERE id = id_video;
	COMMIT;
	SET mensaje = 'Video borrado con éxito';
 END //
 
CREATE PROCEDURE ce(IN nombreN varchar(50), IN generoN varchar(50), IN rendimientoN float, IN estadoN varchar(50), IN urlImagenN varchar(2000), IN id_rol int, OUT mensaje varchar(50)) /* Crear Empleado */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	START TRANSACTION;
		INSERT INTO empleado(nombre, genero, rendimiento, estado, urlImagen, rol_id)
		VALUES(nombreN, generoN, rendimientoN, estadoN, urlImagenN, id_rol);
	COMMIT;
	SET mensaje = 'Empleado guardado con éxito.';
 END //
 
CREATE PROCEDURE be(IN id_empleado int, OUT mensaje varchar(50)) /* Borrar Empleado */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	START TRANSACTION;
		DELETE FROM empleado WHERE id = id_empleado;
	COMMIT;
	SET mensaje = 'Empleado borrado con éxito.';
 END //
 
 CREATE PROCEDURE me(IN id_empleado int, IN nombreN varchar(50), IN generoN varchar(50), IN rendimientoN float, IN estadoN varchar(50), IN urlImagenN varchar(2000), IN id_rol int, OUT mensaje varchar(50)) /* Modificar Empleado */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	START TRANSACTION;
		UPDATE empleado
		SET nombre = nombreN, genero = generoN, rendimiento = rendimientoN, estado = estadoN, urlImagen = urlImagenN, rol_id = id_rol 
		WHERE id = id_empleado;
	COMMIT;
	SET mensaje = 'Datos del empleado actualizados con éxito.';
 END //
 
CREATE PROCEDURE ct(IN HoraInicioN time, IN HoraFinN time, IN id_empleado int, OUT mensaje varchar(50)) /* Crear Turno */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	START TRANSACTION;
		INSERT INTO turno(HoraInicio, HoraFin, empleado_id)
		VALUES(HoraInicioN, HoraFinN, id_empleado);
	COMMIT;
	SET mensaje = 'Turno del empleado asignado con éxito.';
 END //

CREATE PROCEDURE gdt(IN id_turno int, IN id_diaSemana int, OUT mensaje varchar(50)) /* Guardar Días de un Turno */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	START TRANSACTION;
		INSERT INTO diasTurno(turno_id, diaSemana_id)
		VALUES(id_turno, id_diaSemana);
	COMMIT;
	SET mensaje = 'Diás de turnos del empleado asignado con éxito.';
 END //
	
CREATE PROCEDURE bt(IN id_turno int, OUT mensaje varchar(50)) /* Borrar Turno */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	START TRANSACTION;
		DELETE FROM turno WHERE id = id_turno;
	COMMIT;
	SET mensaje = 'Turno del empleado eliminado con éxito.';
 END //
 
CREATE PROCEDURE mt(OUT mensaje varchar(50)) /* Mostrar Turnos */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	SELECT * FROM turno;
	SET mensaje = 'Mostrando todos los turnos...';
 END //
 
CREATE PROCEDURE mte(IN id_empleado int, OUT mensaje varchar(50)) /* Mostrar Turnos de Empleado */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	SELECT * FROM turno WHERE empleado_id = id_empleado;
	SET mensaje = 'Mostrando todos los turnos del empleado seleccionado...';
 END //
 
 /*CREATE PROCEDURE mtrh(IN hora1 time, hora2 time, OUT mensaje varchar(50)) Mostrar Turnos en un Rango de Horas */
 /*BEGIN*/
	/*DECLARE EXIT HANDLER FOR SQLEXCEPTION*/
	 /*BEGIN*/
	  /*ROLLBACK;*/
	  /*SET mensaje = 'Ocurrio un error.';*/
	 /*END;*/
	/*SELECT * FROM turno WHERE empleado_id = id_empleado;*/
	/*SET mensaje = 'Mostrando todos los turnos del empleado seleccionado...'*/
 /*END */
 /*Posible SP en caso de cambiar la tabla de turnos(NO ESTA HECHO TODAVÍA)      TAMBIEN POSIBILIDAD DE UN SP DE MODIFICAR TURNO*/
 
CREATE PROCEDURE gh(IN fechaYHoraEntradaN datetime, fechaYHoraSalidaN datetime, IN id_empleado int, OUT mensaje varchar(50)) /* Guardar Horas */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	START TRANSACTION;
		INSERT INTO horas(fechaYHoraEntrada, fechaYHoraSalida, empleado_id)
		VALUES(fechaYHoraEntradaN, fechaYHoraSalidaN, id_empleado);
	COMMIT;
	SET mensaje = 'Horas guardadas con éxito';
 END //
 
CREATE PROCEDURE vhef(IN id_empleado int, IN fecha date, OUT mensaje varchar(50)) /* Ver Horas de un Empleado en una Fecha */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	SELECT * FROM horas WHERE empleado_id = id_empleado AND DATE(fechaYHoraEntrada) = fecha;
	SET mensaje = 'Mostrando las horas del empleado seleccionado en el día seleccionado...';
 END //
 
CREATE PROCEDURE ghe(IN cantidadN float, IN id_horas int, OUT mensaje varchar(50)) /* Guardar Horas Extra */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	START TRANSACTION;
		INSERT INTO horas_extra(cantidad, horas_id)
		VALUES(cantidadN, id_horas);
	COMMIT;
	SET mensaje = 'Horas extra guardadas con éxito.';
 END //
 
CREATE PROCEDURE ga(IN tipoActividadN varchar(100), IN fechaYHoraComienzoN datetime, IN fechaYHoraFinN datetime, IN id_empleado int, OUT mensaje varchar(50)) /* Guardar Actividad */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	START TRANSACTION;
		INSERT INTO actividad(tipoActividad, fechaYHoraComienzo, fechaYHoraFin, empleado_id)
		VALUES(tipoActividadN, fechaYHoraComienzoN, fechaYHoraFinN, id_empleado);
	COMMIT;
	SET mensaje = 'Actividad guardada con éxito.';
 END //
 
CREATE PROCEDURE ba(IN id_actividad int, OUT mensaje varchar(50)) /* Borrar Actividad */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	START TRANSACTION;
		DELETE FROM actividad WHERE id = id_actividad;
	COMMIT;
	SET mensaje = 'Actividad Borrada.';
 END //
 
 /* Sin SP de métricas hasta corregir o estar seguro que la tabla de métrica esta bien.*/
CREATE PROCEDURE cm(IN tipoN varchar(50), OUT mensaje varchar(50)) /* Crear Métrica */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	START TRANSACTION;
		INSERT INTO metrica(tipo)
		VALUES(tipoN);
	COMMIT;
	SET mensaje = 'Metrica guardada con éxito.';
 END //

CREATE PROCEDURE cdm(IN id_actividad int, IN id_metrica int, OUT mensaje varchar(50)) /* Cargar Datos de una Métrica */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	START TRANSACTION;
		INSERT INTO inforMetrica(actividad_id, metrica_id)
		VALUES(id_actividad, id_metrica);
	COMMIT;
	SET mensaje = 'Dato añadido a la métrica con éxito.';
 END //
		
CREATE PROCEDURE gal(IN gradoN varchar(50), IN incumplimientoN varchar(100), IN fechaYHora datetime, IN id_empleado int, OUT mensaje varchar(50)) /* Guardar Alerta */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	START TRANSACTION;
		INSERT INTO alerta(grado, incumplimiento, fechaYHora, empleado_id)
		VALUES(gradoN, incumplimientoN, fechaYHoraN, id_empleado);
	COMMIT;
	SET mensaje = 'Alerta guardada con éxito.';
 END //
 
CREATE PROCEDURE bal(IN id_alerta int , OUT mensaje varchar(50)) /* Borrar Alerta */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	START TRANSACTION;
		DELETE FROM alerta WHERE id = id_alerta;
	COMMIT;
	SET mensaje = 'Alerta guardada con éxito.';
 END //

CREATE PROCEDURE ghi(IN minutoInicioN time, IN minutoFinN time, IN id_video int, id_actividad int, OUT mensaje varchar(50)) /* Guardar Highlight */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	START TRANSACTION;
		INSERT INTO highlights(minutoInicio, minutoFin, video_id, actividad_id)
		VALUES(minutoInicioN, minutoFinN, id_video, id_actividad);
	COMMIT;
	SET mensaje = 'Highlight guardado con éxito.';
 END //

CREATE PROCEDURE bhi(IN id_highlight, OUT mensaje varchar(50)) /* Borrar Highlight */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	START TRANSACTION;
		DELETE FROM highlights WHERE id = id_highlight;
	COMMIT;
	SET mensaje = 'Highlight guardado con éxito.';
 END //

CREATE PROCEDURE cra(IN estadoRevisionN varchar(50), IN comentarios varchar(200), IN fechaYHoraRevision datetime, IN id_usuario int, IN id_alerta int, OUT mensaje varchar(50)) /* Crear una Revisión de Alerta */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	START TRANSACTION;
		INSERT INTO revision_alerta(estadoRevision, comentarios, fechaYHoraRevision, usuario_id, alerta_id)
		VALUES(estadoRevisionN, comentariosN, fechaYHoraRevisionN, id_usuario, id_alerta)
	COMMIT;
	SET mensaje = 'Revisión de alerta creada con éxito.';
 END //

CREATE PROCEDURE mera(IN id_revision int, IN estadoRevisionN varchar(50), OUT mensaje varchar(50)) /* Modificar el Estado de una Revisión de Alerta */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	START TRANSACTION;
		UPDATE revision_alerta
		SET estadoRevision = estadoRevisionN
	COMMIT;
	SET mensaje = 'Estado de la revisión modificado con éxito.';
 END //

CREATE PROCEDURE gms(IN minutoInicioN time, IN minutoFinN time, IN descripcionPersonaInvolucradaN varchar(500),IN, boundingBoxN varchar(500), id_video int, OUT mensaje varchar(50)) /* Guardar un movimiento sospechoso */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	START TRANSACTION;
		INSERT INTO mov_sospechoso(minutoInicio, minutoFin, descripcionPersonaInvolucrada, boundingBox, video_id)
		VALUES(minutoInicioN, minutoFinN, descripcionPersonaInvolucradaN, boundingBoxN, id_video);
	COMMIT;
	SET mensaje = 'Movimiento sospechoso registrado con éxito.';
 END //

CREATE PROCEDURE bms(IN id_movimiento, OUT mensaje varchar(50)) /* Borrar un movimiento sospechoso */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	START TRANSACTION;
		DELETE FROM mov_sospechoso WHERE id = id_movimiento;
	COMMIT;
	SET mensaje = 'Movimiento sospechoso registrado con éxito.';
 END //
 DELIMITER ;

 DELIMITER //
	/*Triggers de inserts*/
	CREATE TRIGGER trg_after_insert_rolEmpleado
	AFTER INSERT ON rol_empleado
	FOR EACH ROW
	BEGIN
			INSERT INTO auditoria(accion,usuario_id,tablaM,registro_afectado_id,fecha)
			VALUES ('INSERT',@current_user_id, 'rol_empleado', NEW.id,NOW());
	END // 
	
	CREATE TRIGGER trg_after_insert_empleado
	AFTER INSERT ON empleado
	FOR EACH ROW
	BEGIN
			INSERT INTO auditoria(accion,usuario_id,tablaM,registro_afectado_id,fecha)
			VALUES ('INSERT',@current_user_id, 'empleado', NEW.id,NOW());
	END // 

	CREATE TRIGGER trg_after_insert_turno
	AFTER INSERT ON turno
	FOR EACH ROW
	BEGIN
			INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
			VALUES ('INSERT', @current_user_id, 'turno', NEW.id, NOW());
	END //

	CREATE TRIGGER trg_after_insert_horas
	AFTER INSERT ON horas
	FOR EACH ROW
	BEGIN
			INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
			VALUES ('INSERT', @current_user_id, 'horas', NEW.id, NOW());
	END //

	CREATE TRIGGER trg_after_insert_horasExtra
	AFTER INSERT ON horas_extra
	FOR EACH ROW
	BEGIN
			INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
			VALUES ('INSERT', @current_user_id, 'horas_extra', NEW.id, NOW());
	END //

	CREATE TRIGGER trg_after_insert_actividad
	AFTER INSERT ON actividad
	FOR EACH ROW
	BEGIN
			INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
			VALUES ('INSERT', @current_user_id, 'actividad', NEW.id, NOW());
	END //

	CREATE TRIGGER trg_after_insert_metrica
	AFTER INSERT ON metrica
	FOR EACH ROW
	BEGIN
			INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
			VALUES ('INSERT', @current_user_id, 'metrica', NEW.id, NOW());
	END //

	CREATE TRIGGER trg_after_insert_alerta
	AFTER INSERT ON alerta
	FOR EACH ROW
	BEGIN
			INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
			VALUES ('INSERT', @current_user_id, 'alerta', NEW.id, NOW());
	END //

	CREATE TRIGGER trg_after_insert_camara
	AFTER INSERT ON camara
	FOR EACH ROW
	BEGIN
			INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
			VALUES ('INSERT', @current_user_id, 'camara', NEW.id, NOW());
	END //

	CREATE TRIGGER trg_after_insert_video
	AFTER INSERT ON video
	FOR EACH ROW
	BEGIN
			INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
			VALUES ('INSERT', @current_user_id, 'video', NEW.id, NOW());
	END //

	CREATE TRIGGER trg_after_insert_highlights
	AFTER INSERT ON highlights
	FOR EACH ROW
	BEGIN
			INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
			VALUES ('INSERT', @current_user_id, 'highlights', NEW.id, NOW());
	END //

	CREATE TRIGGER trg_after_insert_movSospechoso
	AFTER INSERT ON mov_sospechoso
	FOR EACH ROW
	BEGIN
			INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
			VALUES ('INSERT', @current_user_id, 'mov_sospechoso', NEW.id, NOW());
	END //

	CREATE TRIGGER trg_after_insert_revisionAlerta
	AFTER INSERT ON revision_alerta
	FOR EACH ROW
	BEGIN
			INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
			VALUES ('INSERT', @current_user_id, 'revision_alerta', NEW.id, NOW());
	END //

	CREATE TRIGGER trg_after_insert_usuario
	AFTER INSERT ON usuario
	FOR EACH ROW
	BEGIN
			INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
			VALUES ('INSERT', @current_user_id, 'usuario', NEW.id, NOW());
	END //
	
	/*Triggers de update*/
	CREATE TRIGGER trg_after_update_rolEmpleado
	AFTER UPDATE ON rol_empleado
	FOR EACH ROW
	BEGIN
			INSERT INTO auditoria(accion,usuario_id,tablaM,registro_afectado_id,fecha)
			VALUES ('UPDATE',@current_user_id, 'rol_empleado', NEW.id,NOW());
	END // 
	
	CREATE TRIGGER trg_after_update_empleado
	AFTER UPDATE ON empleado
	FOR EACH ROW
	BEGIN
			INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
			VALUES ('UPDATE', @current_user_id, 'empleado', NEW.id, NOW());
	END //

	CREATE TRIGGER trg_after_update_turno
	AFTER UPDATE ON turno
	FOR EACH ROW
	BEGIN
			INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
			VALUES ('UPDATE', @current_user_id, 'turno', NEW.id, NOW());
	END //

	CREATE TRIGGER trg_after_update_horas
	AFTER UPDATE ON horas
	FOR EACH ROW
	BEGIN
			INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
			VALUES ('UPDATE', @current_user_id, 'horas', NEW.id, NOW());
	END //

	CREATE TRIGGER trg_after_update_horasExtra
	AFTER UPDATE ON horas_extra
	FOR EACH ROW
	BEGIN
			INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
			VALUES ('UPDATE', @current_user_id, 'horas_extra', NEW.id, NOW());
	END //

	CREATE TRIGGER trg_after_update_actividad
	AFTER UPDATE ON actividad
	FOR EACH ROW
	BEGIN
			INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
			VALUES ('UPDATE', @current_user_id, 'actividad', NEW.id, NOW());
	END //

	CREATE TRIGGER trg_after_update_metrica
	AFTER UPDATE ON metrica
	FOR EACH ROW
	BEGIN
			INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
			VALUES ('UPDATE', @current_user_id, 'metrica', NEW.id, NOW());
	END //

	CREATE TRIGGER trg_after_update_alerta
	AFTER UPDATE ON alerta
	FOR EACH ROW
	BEGIN
			INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
			VALUES ('UPDATE', @current_user_id, 'alerta', NEW.id, NOW());
	END //

	CREATE TRIGGER trg_after_update_camara
	AFTER UPDATE ON camara
	FOR EACH ROW
	BEGIN
			INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
			VALUES ('UPDATE', @current_user_id, 'camara', NEW.id, NOW());
	END //

	CREATE TRIGGER trg_after_update_video
	AFTER UPDATE ON video
	FOR EACH ROW
	BEGIN
			INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
			VALUES ('UPDATE', @current_user_id, 'video', NEW.id, NOW());
	END //

	CREATE TRIGGER trg_after_update_highlights
	AFTER UPDATE ON highlights
	FOR EACH ROW
	BEGIN
			INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
			VALUES ('UPDATE', @current_user_id, 'highlights', NEW.id, NOW());
	END //

	CREATE TRIGGER trg_after_update_movSospechoso
	AFTER UPDATE ON mov_sospechoso
	FOR EACH ROW
	BEGIN
			INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
			VALUES ('UPDATE', @current_user_id, 'mov_sospechoso', NEW.id, NOW());
	END //

	CREATE TRIGGER trg_after_update_revisionAlerta
	AFTER UPDATE ON revision_alerta
	FOR EACH ROW
	BEGIN
			INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
			VALUES ('UPDATE', @current_user_id, 'revision_alerta', NEW.id, NOW());
	END //

	CREATE TRIGGER trg_after_update_usuario
	AFTER UPDATE ON usuario
	FOR EACH ROW
	BEGIN
			INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
			VALUES ('UPDATE', @current_user_id, 'usuario', NEW.id, NOW());
	END //
	
	/*Triggers Delete*/
	CREATE TRIGGER trg_after_delete_rolEmpleado
	AFTER DELETE ON rol_empleado
	FOR EACH ROW
	BEGIN
			INSERT INTO auditoria(accion,usuario_id,tablaM,registro_afectado_id,fecha)
			VALUES ('DELATE',@current_user_id, 'rol_empleado', OLD.id,NOW());
	END // 

	CREATE TRIGGER trg_after_delete_empleado
	AFTER DELETE ON empleado
	FOR EACH ROW
	BEGIN
			INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
			VALUES ('DELETE', @current_user_id, 'empleado', OLD.id, NOW());
	END //

	CREATE TRIGGER trg_after_delete_turno
	AFTER DELETE ON turno
	FOR EACH ROW
	BEGIN
			INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
			VALUES ('DELETE', @current_user_id, 'turno', OLD.id, NOW());
	END //

	CREATE TRIGGER trg_after_delete_horas
	AFTER DELETE ON horas
	FOR EACH ROW
	BEGIN
			INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
			VALUES ('DELETE', @current_user_id, 'horas', OLD.id, NOW());
	END //


	CREATE TRIGGER trg_after_delete_horasExtra
	AFTER DELETE ON horas_extra
	FOR EACH ROW
	BEGIN
			INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
			VALUES ('DELETE', @current_user_id, 'horas_extra', OLD.id, NOW());
	END //

	CREATE TRIGGER trg_after_delete_actividad
	AFTER DELETE ON actividad
	FOR EACH ROW
	BEGIN
			INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
			VALUES ('DELETE', @current_user_id, 'actividad', OLD.id, NOW());
	END //

	CREATE TRIGGER trg_after_delete_metrica
	AFTER DELETE ON metrica
	FOR EACH ROW
	BEGIN
			INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
			VALUES ('DELETE', @current_user_id, 'metrica', OLD.id, NOW());
	END //

	CREATE TRIGGER trg_after_delete_alerta
	AFTER DELETE ON alerta
	FOR EACH ROW
	BEGIN
			INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
			VALUES ('DELETE', @current_user_id, 'alerta', OLD.id, NOW());
	END //

	CREATE TRIGGER trg_after_delete_camara
	AFTER DELETE ON camara
	FOR EACH ROW
	BEGIN
			INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
			VALUES ('DELETE', @current_user_id, 'camara', OLD.id, NOW());
	END //

	CREATE TRIGGER trg_after_delete_video
	AFTER DELETE ON video
	FOR EACH ROW
	BEGIN
			INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
			VALUES ('DELETE', @current_user_id, 'video', OLD.id, NOW());
	END //

	CREATE TRIGGER trg_after_delete_highlights
	AFTER DELETE ON highlights
	FOR EACH ROW
	BEGIN
			INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
			VALUES ('DELETE', @current_user_id, 'highlights', OLD.id, NOW());
	END //

	CREATE TRIGGER trg_after_delete_movSospechoso
	AFTER DELETE ON mov_sospechoso
	FOR EACH ROW
	BEGIN
			INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
			VALUES ('DELETE', @current_user_id, 'mov_sospechoso', OLD.id, NOW());
	END //

	CREATE TRIGGER trg_after_delete_revisionAlerta
	AFTER DELETE ON revision_alerta
	FOR EACH ROW
	BEGIN
			INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
			VALUES ('DELETE', @current_user_id, 'revision_alerta', OLD.id, NOW());
	END //

	CREATE TRIGGER trg_after_delete_usuario
	AFTER DELETE ON usuario
	FOR EACH ROW
	BEGIN
			INSERT INTO auditoria(accion, usuario_id, tablaM, registro_afectado_id, fecha)
			VALUES ('DELETE', @current_user_id, 'usuario', OLD.id, NOW());
	END //

 DELIMITER ;
