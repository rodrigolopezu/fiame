"""Tipo de cambio de referencia (soles por dólar).

Se consulta a una API pública y se guarda en la tabla `tipo_cambio`. Si no hay conexión,
se usa el último valor guardado. El vendedor siempre confirma el valor en cada venta.
"""
import json
import urllib.request
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import modelos as m

URL = "https://api.apis.net.pe/v1/tipo-cambio-sunat?fecha={fecha}"


def _consultar(fecha: date) -> tuple[Decimal, Decimal] | None:
    try:
        with urllib.request.urlopen(URL.format(fecha=fecha.isoformat()), timeout=3) as r:
            datos = json.load(r)
        return Decimal(str(datos["compra"])).quantize(Decimal("0.001")), Decimal(str(datos["venta"])).quantize(Decimal("0.001"))
    except Exception:
        return None


def referencia(s: Session, fecha: date) -> m.TipoCambio | None:
    guardado = s.get(m.TipoCambio, fecha)
    if guardado:
        return guardado
    consultado = _consultar(fecha)
    if consultado:
        fila = m.TipoCambio(fecha=fecha, compra=consultado[0], venta=consultado[1], fuente="SUNAT (apis.net.pe)")
        s.add(fila)
        s.commit()
        return fila
    return s.scalar(select(m.TipoCambio).order_by(m.TipoCambio.fecha.desc()).limit(1))
