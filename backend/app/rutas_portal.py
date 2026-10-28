"""Portal del cliente: consulta de solo lectura con el código que le entrega el vendedor."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.bd import sesion
from app.json_exacto import exacto
from app.modelos import Tienda
from app.servicios import clientes, credito, sistema, vistas

router = APIRouter(prefix="/api/portal")


class Consulta(BaseModel):
    codigo: str = Field(min_length=4, max_length=20)


@router.post("")
def consultar(datos: Consulta, s: Session = Depends(sesion)):
    cliente = clientes.buscar_por_codigo(s, datos.codigo)
    if cliente is None:
        raise HTTPException(404, "Código no válido. Verifica el código que te entregó la tienda.")
    hoy = sistema.hoy(s)
    credito.ponerse_al_dia(s, hoy, cliente=cliente)
    detalle = vistas.cliente_detalle(s, cliente, hoy)
    tienda = s.get(Tienda, cliente.tienda_id)
    # Solo lo que le corresponde ver al cliente: sin score ni datos internos de la tienda.
    return exacto({
        "hoy": hoy,
        "tienda": {"nombre": tienda.nombre, "telefono": tienda.telefono, "direccion": tienda.direccion},
        "cliente": {"nombre": detalle.nombre, "moneda": detalle.moneda, "dia_corte": detalle.dia_corte,
                    "dia_pago": detalle.dia_pago},
        "linea": detalle.linea,
        "tasa_compensatoria": detalle.tasa_compensatoria,
        "tasa_moratoria": detalle.tasa_moratoria,
        "deuda_pendiente": detalle.deuda_pendiente,
        "deuda_al_dia": detalle.deuda_al_dia,
        "estados_vencidos": detalle.estados_vencidos,
        "proximo_vencimiento": detalle.proximo_vencimiento,
        "estados_cuenta": detalle.estados_cuenta,
        "ventas": detalle.ventas,
        "pagos": [p for p in detalle.pagos if p.estado == "VALIDO"],
    })
