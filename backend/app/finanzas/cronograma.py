"""Método francés vencido ordinario (R6, R7, R18)."""
from dataclasses import dataclass
from decimal import Decimal

from .redondeo import r2


@dataclass(frozen=True)
class FilaCronograma:
    numero: int
    saldo_inicial: Decimal
    interes: Decimal
    cuota: Decimal
    amortizacion: Decimal
    saldo_final: Decimal


def capitalizar(capital: Decimal, tasa_periodo: Decimal) -> Decimal:
    """Capital más el interés del periodo de gracia total: r2(C · (1 + TE))."""
    return r2(capital * (1 + tasa_periodo))


def cuota_francesa(saldo: Decimal, tep: Decimal, periodos: int) -> Decimal:
    """Cuota vencida sobre el saldo (Fórmulas 49 y 67 del libro).

    R = SI · TEP · (1 + TEP)^k / ((1 + TEP)^k − 1),  con k = periodos restantes.
    """
    factor = (1 + tep) ** periodos
    return r2(saldo * tep * factor / (factor - 1))


def cronograma_frances(capital: Decimal, tep: Decimal, n: int) -> list[FilaCronograma]:
    """Plan de pagos: la cuota se recalcula cada periodo sobre el saldo inicial (R18).

    La última cuota es saldo + interés para que el saldo quede exactamente en cero.
    """
    filas, saldo = [], capital
    for numero in range(1, n + 1):
        interes = r2(saldo * tep)
        if numero == n:
            cuota = saldo + interes
        else:
            cuota = cuota_francesa(saldo, tep, n - numero + 1)
        amortizacion = cuota - interes
        saldo_final = saldo - amortizacion
        filas.append(FilaCronograma(numero, saldo, interes, cuota, amortizacion, saldo_final))
        saldo = saldo_final
    return filas


def liberacion_de_linea(capital: Decimal, amortizaciones: list[Decimal]) -> list[Decimal]:
    """Parte de cada cuota que libera la línea de crédito.

    Cada cuota libera su amortización, pero en total nunca más que el capital de la venta
    (la diferencia es el interés de la gracia capitalizado).
    """
    liberado, resultado = Decimal("0"), []
    for amortizacion in amortizaciones:
        libera = min(amortizacion, capital - liberado)
        liberado += libera
        resultado.append(libera)
    return resultado
