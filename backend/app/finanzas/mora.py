"""Intereses de una compra y por mora (R8, R11, R17)."""
from dataclasses import dataclass
from decimal import Decimal

from .redondeo import r2
from .tasas import Tasa


def interes(base: Decimal, tasa: Tasa, dias: int) -> Decimal:
    """Interés de `base` durante `dias` días: r2(base · TE_dias)."""
    return r2(base * tasa.efectiva(dias))


@dataclass(frozen=True)
class InteresesMora:
    dias: int
    tasa_compensatoria: Decimal
    interes_compensatorio: Decimal
    tasa_moratoria: Decimal
    interes_moratorio: Decimal

    @property
    def total(self) -> Decimal:
        return self.interes_compensatorio + self.interes_moratorio


def intereses_por_mora(exigible: Decimal, compensatoria: Tasa, moratoria: Tasa, dias: int) -> InteresesMora:
    """Compensatorio y moratorio por los días de atraso, ambos sobre el exigible (R17).

    Cada interés se redondea por separado antes de sumarse (R16; libro, ej. 5-36).
    """
    if dias <= 0:
        cero = Decimal("0.00")
        return InteresesMora(0, Decimal("0"), cero, Decimal("0"), cero)
    tc = compensatoria.efectiva(dias)
    tm = moratoria.efectiva(dias)
    return InteresesMora(dias, tc, r2(exigible * tc), tm, r2(exigible * tm))
