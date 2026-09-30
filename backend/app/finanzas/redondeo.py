"""Redondeo del Anexo A (R3, R4, R16).

- Dinero: 2 decimales, half-up.
- Tasas: 7 decimales en porcentaje, es decir 9 decimales como fracción.

Todo el sistema trabaja con `Decimal`; nunca con `float`.
"""
import decimal
from decimal import ROUND_HALF_UP, Decimal

# Precisión de trabajo de las operaciones intermedias (potencias, divisiones).
# DefaultContext es la plantilla de los hilos nuevos, como los del servidor web.
decimal.DefaultContext.prec = 40
decimal.getcontext().prec = 40

CENTIMO = Decimal("0.01")
DECIMALES_TASA = Decimal("0.000000001")  # 7 decimales en porcentaje


def r2(monto: Decimal) -> Decimal:
    """Redondea un monto de dinero a 2 decimales (half-up)."""
    return monto.quantize(CENTIMO, ROUND_HALF_UP)


def r7(tasa: Decimal) -> Decimal:
    """Redondea una tasa (como fracción) a 7 decimales en porcentaje."""
    return tasa.quantize(DECIMALES_TASA, ROUND_HALF_UP)


def a_porcentaje(tasa: Decimal) -> Decimal:
    """0.018087582 -> 1.8087582 (solo para mostrar)."""
    return (tasa * 100).quantize(Decimal("0.0000001"), ROUND_HALF_UP)
