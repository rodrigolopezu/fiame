"""Autenticación común para los tres roles internos de FiaMe."""
from dataclasses import dataclass
from datetime import datetime
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app import modelos as m
from app.bd import sesion
from app.servicios import sistema
from app.servicios.seguridad import crear_token, hash_clave, leer_token, verificar_clave

router = APIRouter(prefix='/api/auth', tags=['Autenticación'])
ROLES = {'SUPERADMIN', 'ADMIN', 'VENDEDOR'}

class Login(BaseModel):
    usuario: str
    clave: str


class CambioClave(BaseModel):
    clave_actual: str
    clave_nueva: str = Field(min_length=12, max_length=128)

@dataclass
class Identidad:
    s: Session
    usuario: m.Usuario


def identidad(authorization: str | None = Header(default=None), s: Session = Depends(sesion)) -> Identidad:
    esquema, _, token = (authorization or '').partition(' ')
    usuario_id = leer_token(token.strip()) if esquema.lower() == 'bearer' and token else None
    usuario = s.get(m.Usuario, usuario_id) if usuario_id is not None else None
    if usuario is None or not usuario.activo or usuario.rol not in ROLES:
        raise HTTPException(401, 'Sesión no válida o vencida')
    if usuario.rol == 'SUPERADMIN':
        if usuario.tienda_id is not None:
            raise HTTPException(403, 'Configuración de SUPERADMIN inválida')
    elif usuario.tienda_id is None or usuario.tienda is None:
        raise HTTPException(403, 'Usuario sin tienda válida')
    elif usuario.tienda.estado != 'ACTIVA':
        # Los tokens no se guardan: al darse de baja la tienda, su personal queda fuera en la siguiente petición.
        raise HTTPException(401, 'La tienda fue dada de baja. La sesión se cerró.')
    return Identidad(s, usuario)


def permitir_roles(*roles: str):
    def verificar(i: Identidad = Depends(identidad)) -> Identidad:
        if i.usuario.rol not in roles:
            raise HTTPException(403, 'No tiene permisos para esta operación')
        return i
    return verificar


def perfil(usuario: m.Usuario) -> dict:
    return {'usuario': usuario.usuario, 'rol': usuario.rol,
            'tienda_id': usuario.tienda_id,
            'tienda': usuario.tienda.nombre if usuario.tienda is not None else None}

@router.post('/login')
def iniciar_sesion(datos: Login, s: Session = Depends(sesion)):
    usuario = s.scalar(select(m.Usuario).where(m.Usuario.usuario == datos.usuario.strip()))
    if usuario is None or not usuario.activo or not verificar_clave(datos.clave, usuario.password_hash):
        raise HTTPException(401, 'Usuario o contraseña incorrectos')
    if usuario.rol not in ROLES or (usuario.rol == 'SUPERADMIN') != (usuario.tienda_id is None):
        raise HTTPException(403, 'Configuración de usuario inválida')
    if usuario.tienda_id is not None and usuario.tienda is None:
        raise HTTPException(403, 'La tienda del usuario no existe')
    if usuario.tienda is not None and usuario.tienda.estado != "ACTIVA":
        raise HTTPException(status_code=403, detail="La tienda está inactiva")
    usuario.ultimo_acceso = datetime.now()
    sistema.auditar(s, usuario, 'LOGIN', 'usuario', usuario.id)
    s.commit()
    return {'token': crear_token(usuario.id), **perfil(usuario)}

@router.get('/me')
def sesion_actual(i: Identidad = Depends(identidad)):
    return perfil(i.usuario)


@router.put('/clave')
def cambiar_clave(datos: CambioClave, i: Identidad = Depends(identidad)):
    if not verificar_clave(datos.clave_actual, i.usuario.password_hash):
        raise HTTPException(400, 'La contraseña actual no es correcta')
    if datos.clave_nueva == datos.clave_actual:
        raise HTTPException(400, 'La contraseña nueva debe ser distinta de la actual')
    i.usuario.password_hash = hash_clave(datos.clave_nueva)
    sistema.auditar(i.s, i.usuario, 'CAMBIAR_CLAVE', 'usuario', i.usuario.id)
    i.s.commit()
    return {'ok': True}
