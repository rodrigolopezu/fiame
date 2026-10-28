"""Contraseñas, sesiones del vendedor y códigos del portal del cliente.

Solo usa la biblioteca estándar: scrypt para las contraseñas y HMAC-SHA256 para firmar
las sesiones. Los códigos del portal se guardan como hash; el código en claro solo se
muestra al generarlo.
"""
import base64
import hashlib
import hmac
import os
import secrets
import time

SECRETO = os.environ.get("FIAME_SECRETO", "fiame-solo-desarrollo").encode()
DURACION_SESION = 12 * 3600
ALFABETO_CODIGO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # sin 0/O ni 1/I


def hash_clave(clave: str) -> str:
    sal = secrets.token_bytes(16)
    derivada = hashlib.scrypt(clave.encode(), salt=sal, n=2**14, r=8, p=1)
    return f"scrypt${sal.hex()}${derivada.hex()}"


def verificar_clave(clave: str, guardada: str) -> bool:
    try:
        _, sal, derivada = guardada.split("$")
    except ValueError:
        return False
    calculada = hashlib.scrypt(clave.encode(), salt=bytes.fromhex(sal), n=2**14, r=8, p=1)
    return hmac.compare_digest(calculada.hex(), derivada)


def _firma(contenido: str) -> str:
    return hmac.new(SECRETO, contenido.encode(), hashlib.sha256).hexdigest()


def crear_token(usuario_id: int) -> str:
    contenido = f"{usuario_id}.{int(time.time()) + DURACION_SESION}"
    return base64.urlsafe_b64encode(f"{contenido}.{_firma(contenido)}".encode()).decode()


def leer_token(token: str) -> int | None:
    """Id del usuario si el token es válido y no venció."""
    try:
        usuario_id, expira, firma = base64.urlsafe_b64decode(token.encode()).decode().split(".")
    except Exception:
        return None
    if not hmac.compare_digest(firma, _firma(f"{usuario_id}.{expira}")) or int(expira) < time.time():
        return None
    return int(usuario_id)


def normalizar_codigo(codigo: str) -> str:
    return "".join(c for c in codigo.upper() if c.isalnum())


def hash_codigo(codigo: str) -> str:
    return hashlib.sha256(normalizar_codigo(codigo).encode()).hexdigest()


def generar_codigo() -> str:
    """Código de acceso al portal, p. ej. 7KQM-4HPD."""
    letras = "".join(secrets.choice(ALFABETO_CODIGO) for _ in range(8))
    return f"{letras[:4]}-{letras[4:]}"
