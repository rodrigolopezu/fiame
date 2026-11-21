"""Administración de vendedores de la tienda del usuario ADMIN."""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app import modelos as m
from app.rutas_auth import Identidad, permitir_roles
from app.servicios.seguridad import hash_clave
from app.servicios.sistema import auditar

router = APIRouter(prefix="/api/admin", tags=["Administración de tienda"])
SoloAdmin = Annotated[Identidad, Depends(permitir_roles("ADMIN"))]

class NuevoVendedor(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    usuario: str = Field(min_length=3, max_length=60, pattern=r"^[a-zA-Z0-9_.-]+$")
    clave: str = Field(min_length=12, max_length=128)

class EstadoVendedor(BaseModel):
    activo: bool

class NuevaClave(BaseModel):
    clave: str = Field(min_length=12, max_length=128)

def verificar_tienda(i: Identidad) -> int:
    tienda = i.usuario.tienda
    if tienda is None or tienda.estado != "ACTIVA":
        raise HTTPException(403, "La tienda no está activa")
    return tienda.id

def vista(u: m.Usuario) -> dict:
    return {"id": u.id, "usuario": u.usuario, "rol": u.rol,
            "tienda_id": u.tienda_id, "activo": u.activo,
            "creado_en": u.creado_en.isoformat() if u.creado_en else None}

@router.get("/vendedores")
def listar(i: SoloAdmin):
    tid = verificar_tienda(i)
    return [vista(u) for u in i.s.scalars(select(m.Usuario).where(
        m.Usuario.tienda_id == tid, m.Usuario.rol == "VENDEDOR"
    ).order_by(m.Usuario.id.desc())).all()]

@router.post("/vendedores", status_code=201)
def crear(datos: NuevoVendedor, i: SoloAdmin):
    tid = verificar_tienda(i)
    if i.s.scalar(select(m.Usuario.id).where(m.Usuario.usuario == datos.usuario)) is not None:
        raise HTTPException(409, "El nombre de usuario ya existe")
    password_hash = hash_clave(datos.clave)
    try:
        vendedor = m.Usuario(usuario=datos.usuario, password_hash=password_hash,
                             rol="VENDEDOR", tienda_id=tid, activo=True)
        i.s.add(vendedor)
        i.s.flush()
        auditar(i.s, i.usuario, "CREAR_VENDEDOR", "usuario", vendedor.id,
                {"usuario": vendedor.usuario}, tienda_id=tid)
        i.s.commit()
        return vista(vendedor)
    except IntegrityError:
        i.s.rollback()
        raise HTTPException(409, "El nombre de usuario ya existe")
    except Exception:
        i.s.rollback()
        raise

@router.patch("/vendedores/{vendedor_id}")
def cambiar_estado(vendedor_id: int, datos: EstadoVendedor, i: SoloAdmin):
    tid = verificar_tienda(i)
    vendedor = i.s.scalar(select(m.Usuario).where(
        m.Usuario.id == vendedor_id,
        m.Usuario.tienda_id == tid,
        m.Usuario.rol == "VENDEDOR"))
    if vendedor is None:
        raise HTTPException(404, "Vendedor no encontrado en su tienda")
    vendedor.activo = datos.activo
    auditar(i.s, i.usuario, "CAMBIAR_ESTADO_VENDEDOR", "usuario", vendedor.id,
            {"activo": vendedor.activo}, tienda_id=tid)
    i.s.commit()
    return vista(vendedor)


@router.put("/vendedores/{vendedor_id}/clave")
def restablecer_clave(vendedor_id: int, datos: NuevaClave, i: SoloAdmin):
    tid = verificar_tienda(i)
    vendedor = i.s.scalar(select(m.Usuario).where(
        m.Usuario.id == vendedor_id, m.Usuario.tienda_id == tid, m.Usuario.rol == "VENDEDOR"))
    if vendedor is None:
        raise HTTPException(404, "Vendedor no encontrado en su tienda")
    vendedor.password_hash = hash_clave(datos.clave)
    auditar(i.s, i.usuario, "RESTABLECER_CLAVE", "usuario", vendedor.id,
            {"usuario": vendedor.usuario}, tienda_id=tid)
    i.s.commit()
    return {"ok": True}
