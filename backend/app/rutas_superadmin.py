"""Gestión de tiendas y administradores, exclusiva del SUPERADMIN."""
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app import modelos as m
from app.finanzas.tasas import Periodo, Tasa as TasaDominio, TipoTasa
from app.rutas_auth import Identidad, permitir_roles
from app.servicios.seguridad import hash_clave
from app.servicios.sistema import auditar

router = APIRouter(prefix="/api/superadmin", tags=["Superadministración"])
SoloSuperadmin = Annotated[Identidad, Depends(permitir_roles("SUPERADMIN"))]


class NuevaTienda(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    nombre: str = Field(min_length=2, max_length=120)
    giro: str = Field(min_length=2, max_length=40)
    documento: str | None = Field(default=None, max_length=11)
    telefono: str | None = Field(default=None, max_length=15)
    direccion: str | None = Field(default=None, max_length=200)
    moneda: str = Field(default="PEN", pattern="^(PEN|USD)$")
    limite_credito: Decimal = Field(default=Decimal("500"), gt=0, max_digits=12, decimal_places=2)
    max_meses: int = Field(default=6, ge=1, le=36)
    dia_corte: int = Field(default=20, ge=1, le=28)
    dia_pago: int = Field(default=26, ge=1, le=28)
    tasa_compensatoria_anual: Decimal = Field(default=Decimal("24"), gt=0, le=1000)
    tasa_moratoria_anual: Decimal = Field(default=Decimal("36"), gt=0, le=1000)
    bloquear_con_vencido: bool = True
    admin_usuario: str = Field(min_length=3, max_length=60, pattern=r"^[a-zA-Z0-9_.-]+$")
    admin_clave: str = Field(min_length=12, max_length=128)


class NuevoAdministrador(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    usuario: str = Field(min_length=3, max_length=60, pattern=r"^[a-zA-Z0-9_.-]+$")
    clave: str = Field(min_length=12, max_length=128)


class EstadoTienda(BaseModel):
    activa: bool


class NuevaClave(BaseModel):
    clave: str = Field(min_length=12, max_length=128)


def vista_tienda(t: m.Tienda) -> dict:
    return {"id": t.id, "nombre": t.nombre, "giro": t.giro, "documento": t.documento,
            "estado": t.estado, "telefono": t.telefono, "direccion": t.direccion}


def _usuario_libre(i: Identidad, nombre: str):
    if i.s.scalar(select(m.Usuario.id).where(m.Usuario.usuario == nombre)) is not None:
        raise HTTPException(409, "El nombre de usuario ya está registrado")


def _tasa(i: Identidad, valor: Decimal) -> m.Tasa:
    tasa = m.Tasa.desde_dominio(TasaDominio(TipoTasa.EFECTIVA, Periodo.ANUAL, valor))
    i.s.add(tasa)
    i.s.flush()
    return tasa


@router.get("/tiendas")
def listar_tiendas(i: SoloSuperadmin):
    tiendas = i.s.scalars(select(m.Tienda).order_by(m.Tienda.id.desc())).all()
    return [vista_tienda(t) for t in tiendas]


@router.get("/tiendas/{tienda_id}/administradores")
def listar_administradores(tienda_id: int, i: SoloSuperadmin):
    if i.s.get(m.Tienda, tienda_id) is None:
        raise HTTPException(404, "Tienda no encontrada")
    usuarios = i.s.scalars(select(m.Usuario).where(m.Usuario.tienda_id == tienda_id,
                        m.Usuario.rol == "ADMIN").order_by(m.Usuario.id)).all()
    return [{"id": u.id, "usuario": u.usuario, "activo": u.activo} for u in usuarios]


@router.post("/tiendas", status_code=201)
def crear_tienda(datos: NuevaTienda, i: SoloSuperadmin):
    _usuario_libre(i, datos.admin_usuario)
    if datos.documento and i.s.scalar(select(m.Tienda.id).where(m.Tienda.documento == datos.documento)) is not None:
        raise HTTPException(409, "Ya existe una tienda con ese documento")
    # Calcular el hash antes de iniciar las escrituras.
    clave_hash = hash_clave(datos.admin_clave)
    try:
        tienda = m.Tienda(nombre=datos.nombre, giro=datos.giro, documento=datos.documento or None,
                          telefono=datos.telefono or None, direccion=datos.direccion or None)
        i.s.add(tienda)
        i.s.flush()
        comp = _tasa(i, datos.tasa_compensatoria_anual)
        mora = _tasa(i, datos.tasa_moratoria_anual)
        i.s.add(m.ConfiguracionTienda(
            tienda_id=tienda.id, moneda=datos.moneda, limite_credito=datos.limite_credito,
            max_meses=datos.max_meses, dia_corte=datos.dia_corte, dia_pago=datos.dia_pago,
            tasa_compensatoria_id=comp.id, tasa_moratoria_id=mora.id,
            bloquear_con_vencido=datos.bloquear_con_vencido))
        admin = m.Usuario(usuario=datos.admin_usuario, password_hash=clave_hash,
                          rol="ADMIN", tienda_id=tienda.id, activo=True)
        i.s.add(admin)
        i.s.flush()
        auditar(i.s, i.usuario, "CREAR_TIENDA", "tienda", tienda.id,
                {"nombre": tienda.nombre, "admin_id": admin.id}, tienda_id=tienda.id)
        i.s.commit()
        return {"tienda": vista_tienda(tienda), "administrador": {"id": admin.id, "usuario": admin.usuario}}
    except IntegrityError:
        i.s.rollback()
        raise HTTPException(409, "La tienda o el usuario ya existen")
    except Exception:
        i.s.rollback()
        raise


@router.post("/tiendas/{tienda_id}/administradores", status_code=201)
def crear_administrador(tienda_id: int, datos: NuevoAdministrador, i: SoloSuperadmin):
    tienda = i.s.get(m.Tienda, tienda_id)
    if tienda is None:
        raise HTTPException(404, "Tienda no encontrada")
    if tienda.estado != "ACTIVA":
        raise HTTPException(409, "No se pueden agregar administradores a una tienda inactiva")
    _usuario_libre(i, datos.usuario)
    clave_hash = hash_clave(datos.clave)
    try:
        admin = m.Usuario(usuario=datos.usuario, password_hash=clave_hash,
                          rol="ADMIN", tienda_id=tienda.id, activo=True)
        i.s.add(admin)
        i.s.flush()
        auditar(i.s, i.usuario, "CREAR_ADMIN", "usuario", admin.id,
                {"usuario": admin.usuario}, tienda_id=tienda.id)
        i.s.commit()
        return {"id": admin.id, "usuario": admin.usuario, "tienda_id": tienda.id, "rol": admin.rol}
    except IntegrityError:
        i.s.rollback()
        raise HTTPException(409, "El nombre de usuario ya está registrado")
    except Exception:
        i.s.rollback()
        raise


@router.patch("/tiendas/{tienda_id}/estado")
def cambiar_estado_tienda(tienda_id: int, datos: EstadoTienda, i: SoloSuperadmin):
    """Da de baja o reactiva una tienda. En la baja, su personal pierde el acceso de inmediato
    (las sesiones abiertas dejan de servir) y el portal de sus clientes se bloquea; no se borra nada."""
    tienda = i.s.get(m.Tienda, tienda_id)
    if tienda is None:
        raise HTTPException(404, "Tienda no encontrada")
    tienda.estado = "ACTIVA" if datos.activa else "INACTIVA"
    tienda.fecha_baja = None if datos.activa else datetime.now()
    auditar(i.s, i.usuario, "REACTIVAR_TIENDA" if datos.activa else "BAJA_TIENDA", "tienda", tienda.id,
            {"nombre": tienda.nombre}, tienda_id=tienda.id)
    i.s.commit()
    return vista_tienda(tienda)


@router.put("/tiendas/{tienda_id}/administradores/{admin_id}/clave")
def restablecer_clave_administrador(tienda_id: int, admin_id: int, datos: NuevaClave, i: SoloSuperadmin):
    admin = i.s.scalar(select(m.Usuario).where(m.Usuario.id == admin_id, m.Usuario.tienda_id == tienda_id,
                                               m.Usuario.rol == "ADMIN"))
    if admin is None:
        raise HTTPException(404, "Administrador no encontrado en esa tienda")
    admin.password_hash = hash_clave(datos.clave)
    auditar(i.s, i.usuario, "RESTABLECER_CLAVE", "usuario", admin.id, {"usuario": admin.usuario}, tienda_id=tienda_id)
    i.s.commit()
    return {"ok": True}
