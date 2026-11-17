"""Consultas de clientes por administradores; aislamiento por tienda."""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from app import modelos as m
from app.rutas_auth import Identidad, permitir_roles

router = APIRouter(prefix="/api/admin/clientes", tags=["Clientes de tienda (administrador)"])
SoloAdmin = Annotated[Identidad, Depends(permitir_roles("ADMIN"))]

def tienda_activa(i: Identidad) -> int:
    tienda = i.usuario.tienda
    if tienda is None or tienda.estado != "ACTIVA":
        raise HTTPException(403, "La tienda no está activa")
    return tienda.id

def resumen(c: m.Cliente) -> dict:
    return {"id": c.id, "nombres": c.nombres, "apellidos": c.apellidos,
            "tipo_documento": c.tipo_documento, "numero_documento": c.numero_documento,
            "estado": c.estado, "moneda": c.moneda,
            "limite_credito": str(c.limite_credito)}

@router.get("")
def listar(i: SoloAdmin):
    tid = tienda_activa(i)
    clientes = i.s.scalars(select(m.Cliente).where(m.Cliente.tienda_id == tid)
                           .order_by(m.Cliente.apellidos, m.Cliente.nombres)).all()
    return [resumen(c) for c in clientes]

@router.get("/{cliente_id}")
def detalle(cliente_id: int, i: SoloAdmin):
    tid = tienda_activa(i)
    cliente = i.s.scalar(select(m.Cliente).where(m.Cliente.id == cliente_id,
                                                  m.Cliente.tienda_id == tid))
    if cliente is None:
        raise HTTPException(404, "Cliente no encontrado en su tienda")
    return resumen(cliente)
