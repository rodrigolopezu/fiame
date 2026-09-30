"""Fechas del ciclo de crédito (R9, R15 y sección 3 de la especificación)."""
import calendar
from datetime import date


def dias_entre(desde: date, hasta: date) -> int:
    """Días calendario exactos entre dos fechas (R15)."""
    return (hasta - desde).days


def sumar_meses(fecha: date, meses: int) -> date:
    """Misma fecha `meses` meses después. Si el día no existe, usa el último del mes."""
    total = fecha.month - 1 + meses
    anio, mes = fecha.year + total // 12, total % 12 + 1
    dia = min(fecha.day, calendar.monthrange(anio, mes)[1])
    return date(anio, mes, dia)


def fecha_pago_del_corte(corte: date, dia_pago: int) -> date:
    """Primera fecha con el día de pago que sea posterior al corte."""
    pago = date(corte.year, corte.month, dia_pago)
    return pago if pago > corte else sumar_meses(pago, 1)


def calcular_ciclo(fecha_compra: date, dia_corte: int, dia_pago: int) -> tuple[date, date]:
    """Fecha de corte y fecha de pago del ciclo en que cae una compra.

    El corte es a las 23:59:59: una compra del mismo día de corte entra en ese ciclo.
    Una compra posterior al corte pasa al ciclo siguiente (R9).
    """
    corte = date(fecha_compra.year, fecha_compra.month, dia_corte)
    if fecha_compra > corte:
        corte = sumar_meses(corte, 1)
    return corte, fecha_pago_del_corte(corte, dia_pago)
