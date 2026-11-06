"""El antiguo cargador fue deshabilitado para proteger datos reales de Turso.

La versión anterior borraba tablas de producción antes de insertar datos de
prueba. Este módulo ya no crea, actualiza ni elimina registros.
"""


async def cargar_datos_semilla_produccion() -> None:
    raise RuntimeError(
        "La carga semilla está deshabilitada: no se borran ni se escriben datos de prueba en Turso."
    )


if __name__ == "__main__":
    print("Carga semilla deshabilitada. No se contactó ni modificó Turso.")
