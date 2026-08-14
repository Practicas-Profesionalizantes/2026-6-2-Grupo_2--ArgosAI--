import libsql_client

# ============================================================
# CREDENCIALES REALES DE PRODUCCIÓN — MOTOR DE LIMPIEZA AUTOMÁTICO
# ============================================================

URL_RAW = "libsql://basededatoshost-marto.aws-us-west-2.turso.io"
TURSO_TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3ODY3MzcxNDIsImlkIjoiMDFhMDAxMzgtY2MwMS03MzY1LTliOGItODdjNDIwYTgxMGQ5Iiwia2lkIjoiT2p5NDA0bWZXNFNjenpLcnpERThNOEFRVVE5MW9jQ0pHRnZXeEN3czZqWSIsInJpZCI6ImMzMDc4Y2JkLTBkNTYtNGJhNS05MTE0LWIwNjQ4YjU4Yzg3NCJ9.YZieaBW-wZQeAAY-hMsf7FPXBuxl4rbpzOFiEzgnJPpJrc9bw7iOJs2qvbKDWnJk_mGg3V61xQyFJVluCBd7DQ"

# El limpiador matemático: remueve prefijos y garantiza que el host quede intacto
HOST_LIMPIO = URL_RAW.replace("libsql://", "").replace("https://", "").replace("http://", "").strip()

# Construimos la URL en formato HTTPS nativo robusto para AWS
TURSO_URL = f"https://{HOST_LIMPIO}"

def obtener_cliente_turso():
    """
    Retorna el cliente HTTP oficial seguro e independiente de Turso Cloud.
    """
    return libsql_client.create_client(url=TURSO_URL, auth_token=TURSO_TOKEN)
