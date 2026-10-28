"""Reloj del sistema y bitácora de auditoría.

El reloj permite, solo en desarrollo, adelantar la fecha del sistema para probar cortes,
vencimientos y mora sin esperar días reales. La fecha nunca retrocede.
"""
from datetime import date

from sqlalchemy.orm import Session

from app.dominio import ReglaDeNegocio
from app.modelos import Auditoria, Sistema, Usuario

CLAVE_FECHA = "fecha_simulada"


def fecha_real() -> date:
    return date.today()


def hoy(s: Session) -> date:
    """Fecha de trabajo: la simulada si se adelantó el reloj; si no, la real."""
    registro = s.get(Sistema, CLAVE_FECHA)
    real = fecha_real()
    if registro is None:
        return real
    return max(real, date.fromisoformat(registro.valor))


def avanzar(s: Session, fecha: date, usuario: Usuario | None = None) -> date:
    actual = hoy(s)
    if fecha < actual:
        raise ReglaDeNegocio(f"La fecha del sistema no puede retroceder (hoy es {actual:%d/%m/%Y})")
    registro = s.get(Sistema, CLAVE_FECHA) or Sistema(clave=CLAVE_FECHA, valor="")
    registro.valor = fecha.isoformat()
    s.add(registro)
    auditar(s, usuario, "AVANZAR_FECHA", "sistema", None, {"desde": actual.isoformat(), "hasta": fecha.isoformat()})
    return fecha


def auditar(s: Session, usuario: Usuario | None, accion: str, entidad: str, entidad_id: int | None,
            datos: dict | None = None, tienda_id: int | None = None):
    """Registra una operación en la bitácora (requisito del enunciado)."""
    s.add(Auditoria(
        usuario_id=usuario.id if usuario else None,
        tienda_id=tienda_id if tienda_id is not None else (usuario.tienda_id if usuario else None),
        accion=accion, entidad=entidad, entidad_id=entidad_id, datos=datos,
    ))
