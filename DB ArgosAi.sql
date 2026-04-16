CREATE DATABASE ARGOSAI;

USE ARGOSAI;

CREATE TABLE usuario(
	id int primary key,
	nombre varchar(50),
	email varchar(50),
	contrasenia varchar(50),
	telefono varchar(50)  /* Contar la cantidad de dígitos */
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
	estadoProcesamiento varchar(50), /* Tiempo límite*/
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
	vectorFacial varchar(1000), /* No se como son los datos así que le puse 1000 de caracteres por las dudas */ /* averiguar cuanta cantidad */ /* Se puede cambiar por url de la imagen de la persona para que la IA no se reentrene al cambio de cada empleado */
	rol_id int,
	FOREIGN KEY (rol_id) REFERENCES rol_empleado(id)
);
CREATE TABLE turno( /* Pienso que debería cambiar el fechayhorainicio y fechayhorafin por simplemente la hora y el inicio, sin poner una fecha y poner un atributo mas para ver los días que trabaja */ /* Posibilidad de crear otra tabla para los días que trabaja */
	id int primary key,
	fechaYHoraInicio datetime,
	fechaYHoraFin datetime,
	empleado_id int,
	foreign key (empleado_id) REFERENCES empleado(id)
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
	nivelConfianza float, /* No se si esto iría acá. Yo lo sacaría pero por ahora lo dejo. */
	empleado_id int,
	camara_id int, /* Camara id no debería ir en highlights?? */
	FOREIGN KEY (empleado_id) REFERENCES empleado(id),
	FOREIGN KEY (camara_id) REFERENCES camara(id)
);
/* Tabla muchos a muchos relacionamiento entre actividad y métrica */
CREATE TABLE metrica(
	id int primary key,
	tipo varchar(50),
	cantidadRealizada float,
	actividad_id int,
	foreign key (actividad_id) REFERENCES actividad(id) /* Siento que esto no iría porque una métrica reune varias actividades, no una sola*/
);
CREATE TABLE alerta(
	id int primary key,
	grado varchar(50),
	incumplimiento varchar(100),
	fechaYHora datetime,
	nivelConfianza float, /* Lo mismo que en Actividad, no se si iría esto acá */
	empleado_id int,
	camara_id int, /* Camara id no debería ir en highlights?? */
	FOREIGN KEY (empleado_id) REFERENCES empleado(id),
	FOREIGN KEY (camara_id)	REFERENCES camara(id)
);
CREATE TABLE highlights( /* No habría que extraer un nuevo video para el highlight??? si no puede ser poner el fragmento(de que minuto a que minuto del video dura)*/ 
	id int primary key,
	/* añadir marca de tiempo del highlight */
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
	fechaYHora datetime,
	descripcionPersonaInvolucrada varchar(500),
	nivelConfianza float, /* Lo mismo que en Actividad y Alerta, no se si iría esto acá */
	boundingBox varchar(500), /* El cuadro con el que la IA detecta el movimiento. */
	highlight_id int, /* Highlight es para las actividades, no tendría que tener su propio video o en todo caso foreign key de video?? */ 
	/* Añadir marca de tiempo, borrar highlight id y meter id del video */ 
	FOREIGN KEY (highlight_id) REFERENCES highlights(id)
);

/* Pendiente generar inserts para los roles de los empleados*/

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
	SET mensaje = 'Usuario creado con éxito.'
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
	SET mensaje = 'Cámara guardada con éxito.'
 END //
 
CREATE PROCEDURE vtc(OUT mensaje varchar(50)) /* Ver todas las cámaras */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	SELECT * FROM camara;
	SET mensaje = 'Mostrando cámaras..'
 END //
 
CREATE PROCEDURE vdc(IN id_camara int, OUT mensaje varchar(50)) /* Ver datos de una cámara */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	SELECT * FROM camara WHERE id = id_camara;
	SET mensaje = CONCAT('Mostrando datos de la cámara con el id .', id_camara)
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
	SET mensaje = 'Cámara borrada con éxito.'
 END //
 
 CREATE PROCEDURE mc(IN id_camara int, IN ubicacionN varchar(50), IN estadoN(50), IN direccionIPN(50), OUT mensaje varchar(50)) /* Modificar Cámara */
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
	SET mensaje = 'Cámara modificada con éxito.'
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
	SET mensaje = 'Video guardado con éxito.'
 END //
 
CREATE PROCEDURE mv(OUT mensaje varchar(50)) /* Mostrar Videos */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	SELECT * FROM video;
	SET mensaje = 'Mostrando videos...'
 END //
 
 /* Pendiente crear un SP para borrar videos cuando se cumpla el plazo límite.*/
 
CREATE PROCEDURE ce(IN nombreN varchar(50), IN generoN varchar(50), IN rendimientoN float, IN estadoN varchar(50), IN vectorFacialN varchar(1000), IN id_rol int, OUT mensaje varchar(50)) /* Crear Empleado */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	START TRANSACTION;
		INSERT INTO empleado(nombre, genero, rendimiento, estado, vectorFacial, rol_id)
		VALUES(nombreN, generoN, rendimientoN, estadoN, vectorFacialN, id_rol);
	COMMIT;
	SET mensaje = 'Empleado guardado con éxito.'
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
	SET mensaje = 'Empleado borrado con éxito.'
 END //
 
 CREATE PROCEDURE me(IN id_empleado int, IN nombreN varchar(50), IN generoN varchar(50), IN rendimientoN float, IN estadoN varchar(50), IN vectorFacialN varchar(1000), IN id_rol int, OUT mensaje varchar(50)) /* Modificar Empleado */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	START TRANSACTION;
		UPDATE empleado
		SET nombre = nombreN, genero = generoN, rendimiento = rendimientoN, estado = estadoN, vectorFacial = vectorFacialN, rol_id = id_rol 
		WHERE id = id_empleado;
	COMMIT;
	SET mensaje = 'Datos del empleado actualizados con éxito.'
 END //
 
CREATE PROCEDURE ct(IN fechaYHoraInicioN datetime, IN fechaYHoraFinN datetime, IN id_empleado int, OUT mensaje varchar(50)) /* Crear Turno */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	START TRANSACTION;
		INSERT INTO turno(fechaYHoraInicio, fechaYHoraFin, empleado_id)
		VALUES(fechaYHoraInicioN, fechaYHoraFinN, id_empleado);
	COMMIT;
	SET mensaje = 'Turno del empleado asignado con éxito.'
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
	SET mensaje = 'Turno del empleado eliminado con éxito.'
 END //
 
CREATE PROCEDURE mt(OUT mensaje varchar(50)) /* Mostrar Turnos */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	SELECT * FROM turno;
	SET mensaje = 'Mostrando todos los turnos...'
 END //
 
CREATE PROCEDURE mte(IN id_empleado, OUT mensaje varchar(50)) /* Mostrar Turnos de Empleado */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	SELECT * FROM turno WHERE empleado_id = id_empleado;
	SET mensaje = 'Mostrando todos los turnos del empleado seleccionado...'
 END //
 
 /*
 CREATE PROCEDURE mtrh(IN hora1 time, hora2 time, OUT mensaje varchar(50)) /* Mostrar Turnos en un Rango de Horas */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	SELECT * FROM turno WHERE empleado_id = id_empleado;
	SET mensaje = 'Mostrando todos los turnos del empleado seleccionado...'
 END //
 Posible SP en caso de cambiar la tabla de turnos(NO ESTA HECHO TODAVÍA)      TAMBIEN POSIBILIDAD DE UN SP DE MODIFICAR TURNO*/
 
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
	SET mensaje = 'Horas guardadas con éxito'
 END //
 
CREATE PROCEDURE vhef(IN id_empleado int, IN fecha date, OUT mensaje varchar(50)) /* Ver Horas de un Empleado en una Fecha */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	SELECT * FROM horas WHERE empleado_id = id_empleado AND DATE(fechaYHoraEntrada) = fecha;
	SET mensaje = 'Mostrando las horas del empleado seleccionado en el día seleccionado...'
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
	SET mensaje = 'Horas extra guardadas con éxito.'
 END //
 
CREATE PROCEDURE ga(IN tipoActividadN varchar(100), IN fechaYHoraComienzoN datetime, IN fechaYHoraFinN datetime, IN nivelConfianzaN float, IN id_empleado int, IN id_camara int, OUT mensaje varchar(50)) /* Guardar Actividad */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	START TRANSACTION;
		INSERT INTO actividad(tipoActividad, fechaYHoraComienzo, fechaYHoraFin, nivelConfianza, empleado_id, camara_id)
		VALUES(tipoActividadN, fechaYHoraComienzoN, fechaYHoraFinN, nivelConfianzaN, id_empleado, id_camara);
	COMMIT;
	SET mensaje = 'Actividad guardada con éxito.'
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
	SET mensaje = 'Actividad Borrada.'
 END //
 
 /* Sin SP de métricas hasta corregir o estar seguro que la tabla de métrica esta bien.*/
 
CREATE PROCEDURE gal(IN gradoN varchar(50), IN incumplimientoN varchar(100), IN fechaYHora datetime, IN nivelConfianzaN float, IN id_empleado int, IN id_camara int, OUT mensaje varchar(50)) /* Guardar Alerta */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	START TRANSACTION;
		INSERT INTO alerta(grado, incumplimiento, fechaYHora, nivelConfianza, empleado_id, camara_id)
		VALUES(gradoN, incumplimientoN, fechaYHoraN, nivelConfianzaN, id_empleado, id_camara);
	COMMIT;
	SET mensaje = 'Alerta guardada con éxito.'
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
	SET mensaje = 'Alerta guardada con éxito.'
 END //

CREATE PROCEDURE gh(IN id_video int, id_actividad int, OUT mensaje varchar(50)) /* Guardar Highlight */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	START TRANSACTION;
		INSERT INTO highlights(video_id, actividad_id)
		VALUES(id_video, id_actividad);
	COMMIT;
	SET mensaje = 'Highlight guardado con éxito.'
 END //

CREATE PROCEDURE bh(IN id_highlight, OUT mensaje varchar(50)) /* Borrar Highlight */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	START TRANSACTION;
		DELETE FROM highlights WHERE id = id_highlight;
	COMMIT;
	SET mensaje = 'Highlight guardado con éxito.'
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
	SET mensaje = 'Revisión de alerta creada con éxito.'
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
	SET mensaje = 'Estado de la revisión modificado con éxito.'
 END //		

CREATE PROCEDURE gms(IN fechaYHoraN datetime, IN descripcionPersonaInvolucradaN varchar(500), IN nivelConfianzaN float, IN, boundingBoxN varchar(500), id_highlight int, OUT mensaje varchar(50)) /* Guardar un movimiento sospechoso */
 BEGIN
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	 BEGIN
	  ROLLBACK;
	  SET mensaje = 'Ocurrio un error.';
	 END;
	START TRANSACTION;
		INSERT INTO mov_sospechoso(fechaYHora, descripcionPersonaInvolucrada, nivelConfianza, boundingBox, highlight_id)
		VALUES(fechaYHoraN, descripcionPersonaInvolucradaN, nivelConfianzaN, boundingBoxN, id_highlight);
	COMMIT;
	SET mensaje = 'Movimiento sospechoso registrado con éxito.'
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
	SET mensaje = 'Movimiento sospechoso registrado con éxito.'
 END //
 DELIMITER ;
