"""Tasas de interés y su conversión (R2, R12, R13, R19).

Toda tasa se convierte **directamente** a la tasa efectiva del plazo que se necesita,
con un solo exponente (R12). Nunca se pasa primero a tasa diaria.
"""
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from .redondeo import r7

DIAS_ANIO = 360
DIAS_MES = 30


class TipoTasa(str, Enum):
    EFECTIVA = "EFECTIVA"
    NOMINAL = "NOMINAL"


class Periodo(str, Enum):
    ANUAL = "ANUAL"
    SEMESTRAL = "SEMESTRAL"
    CUATRIMESTRAL = "CUATRIMESTRAL"
    TRIMESTRAL = "TRIMESTRAL"
    BIMESTRAL = "BIMESTRAL"
    MENSUAL = "MENSUAL"
    QUINCENAL = "QUINCENAL"
    DIARIA = "DIARIA"

    @property
    def dias(self) -> int:
        return DIAS_POR_PERIODO[self]


DIAS_POR_PERIODO = {
    Periodo.ANUAL: 360,
    Periodo.SEMESTRAL: 180,
    Periodo.CUATRIMESTRAL: 120,
    Periodo.TRIMESTRAL: 90,
    Periodo.BIMESTRAL: 60,
    Periodo.MENSUAL: 30,
    Periodo.QUINCENAL: 15,
    Periodo.DIARIA: 1,
}


@dataclass(frozen=True)
class Tasa:
    """Una tasa tal como fue pactada. `valor` está en porcentaje (24 = 24 %)."""

    tipo: TipoTasa
    periodo: Periodo
    valor: Decimal
    capitalizacion: Periodo | None = None

    def __post_init__(self):
        if self.valor <= 0:
            raise ValueError("La tasa debe ser mayor que cero")
        if self.tipo == TipoTasa.EFECTIVA and self.capitalizacion is not None:
            raise ValueError("Una tasa efectiva no lleva periodo de capitalización")
        if self.tipo == TipoTasa.NOMINAL:
            if self.capitalizacion is None:
                # R19: si no se indica capitalización, se asume diaria.
                object.__setattr__(self, "capitalizacion", Periodo.DIARIA)
            if self.capitalizacion.dias > self.periodo.dias:
                raise ValueError("La capitalización no puede ser mayor que el periodo de la tasa")

    def efectiva(self, dias: int) -> Decimal:
        """Tasa efectiva para `dias` días, como fracción redondeada a 7 decimales en %.

        Efectiva de p días (Fórmula 19):  TEP = (1 + TE)^(dias / p) − 1
        Nominal de p días con capitalización de c días (Fórmula 18):
            m = p / c,  TEP = (1 + TN / m)^(dias / c) − 1
        """
        p = Decimal(self.periodo.dias)
        v = self.valor / 100
        if self.tipo == TipoTasa.EFECTIVA:
            return r7((1 + v) ** (Decimal(dias) / p) - 1)
        c = Decimal(self.capitalizacion.dias)
        m = p / c
        return r7((1 + v / m) ** (Decimal(dias) / c) - 1)

    def tea(self) -> Decimal:
        """TEA equivalente, la que se informa al cliente (R14)."""
        return self.efectiva(DIAS_ANIO)

    def tem(self) -> Decimal:
        return self.efectiva(DIAS_MES)

    def descripcion(self) -> str:
        abreviatura = {
            Periodo.ANUAL: "A", Periodo.SEMESTRAL: "S", Periodo.CUATRIMESTRAL: "C",
            Periodo.TRIMESTRAL: "T", Periodo.BIMESTRAL: "B", Periodo.MENSUAL: "M",
            Periodo.QUINCENAL: "Q", Periodo.DIARIA: "D",
        }[self.periodo]
        valor = f"{self.valor.normalize():f} %"
        if self.tipo == TipoTasa.EFECTIVA:
            return f"TE{abreviatura} {valor}"
        return f"TN{abreviatura} {valor} c. {self.capitalizacion.value.lower()}"


def nominal_equivalente(tep: Decimal, dias_tep: int, periodo: Periodo, capitalizacion: Periodo) -> Decimal:
    """Tasa nominal equivalente a una tasa efectiva (Fórmula 17), como fracción r7.

    TN = m · [(1 + TEP)^(c / dias_tep) − 1],  con m = p / c.
    """
    p = Decimal(periodo.dias)
    c = Decimal(capitalizacion.dias)
    if c > p:
        raise ValueError("La capitalización no puede ser mayor que el periodo de la tasa")
    m = p / c
    return r7(m * ((1 + tep) ** (c / Decimal(dias_tep)) - 1))
