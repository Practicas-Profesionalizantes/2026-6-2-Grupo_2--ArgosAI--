import libsql_client

# Credenciales de acceso a tu clúster en la nube de Turso
TURSO_URL = "libsql://tu-base-de-datos-usuario.turso.io"
TURSO_TOKEN = "tu_token_secreto_aqui"

def obtener_cliente_turso():
    """
    Retorna un cliente nativo HTTP de Turso distribuido.
    Siempre debe invocarse mediante bloques 'with' para asegurar el cierre de sockets.
    """
    return libsql_client.create_client(url=TURSO_URL, auth_token=TURSO_TOKEN)
