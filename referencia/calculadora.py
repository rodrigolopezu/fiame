"""Calculadora de referencia de FiaMe.

Implementa docs/especificacion-financiera.md con aritmética decimal exacta. Sirve para
calcular los casos de prueba del informe y como oráculo para los tests de la aplicación.
"""
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().prec = 40

DIAS_ANIO = 360
DIAS_PERIODO = {
    "anual": 360, "semestral": 180, "cuatrimestral": 120, "trimestral": 90,
    "bimestral": 60, "mensual": 30, "quincenal": 15, "diaria": 1,
}


def r2(x: Decimal) -> Decimal:
    """Dinero: 2 decimales, half-up (R3)."""
    return x.quantize(Decimal("0.01"), ROUND_HALF_UP)


def r7(x: Decimal) -> Decimal:
    """Tasa: 7 decimales en porcentaje = 9 decimales como fracción (R4)."""
    return x.quantize(Decimal("0.000000001"), ROUND_HALF_UP)


@dataclass(frozen=True)
class Tasa:
    tipo: str                    # "efectiva" | "nominal"
    periodo: str                 # clave de DIAS_PERIODO
    valor: Decimal               # en porcentaje, p. ej. Decimal("24")
    capitalizacion: str = "diaria"  # solo para nominal (R19)

    def efectiva(self, dias: int) -> Decimal:
        """Tasa efectiva para `dias` días, convertida en un solo paso (R12)."""
        p = DIAS_PERIODO[self.periodo]
        v = self.valor / 100
        if self.tipo == "efectiva":
            return r7((1 + v) ** (Decimal(dias) / p) - 1)
        c = DIAS_PERIODO[self.capitalizacion]
        m = Decimal(p) / c
        return r7((1 + v / m) ** (Decimal(dias) / c) - 1)

    def tea(self) -> Decimal:
        return self.efectiva(DIAS_ANIO)


def pct(x: Decimal) -> str:
    return f"{x * 100:.7f} %"


def dias(desde: date, hasta: date) -> int:
    """Días calendario exactos (R15)."""
    return (hasta - desde).days


def interes(base: Decimal, tasa: Tasa, n_dias: int) -> Decimal:
    return r2(base * tasa.efectiva(n_dias))


def cronograma_frances(capital: Decimal, tasa: Tasa, n: int):
    """Cuota recalculada cada periodo sobre el saldo inicial (Fórmula 67, R18)."""
    tem = tasa.efectiva(30)
    filas, si = [], capital
    for nc in range(1, n + 1):
        k = n - nc + 1
        f = (1 + tem) ** k
        i = r2(si * tem)
        cuota = si + i if nc == n else r2(si * tem * f / (f - 1))
        amort = cuota - i
        sf = si - amort
        filas.append({"nc": nc, "si": si, "interes": i, "cuota": cuota,
                      "amort": amort, "sf": sf})
        si = sf
    return tem, filas


def mora(base: Decimal, comp: Tasa, morat: Tasa, n_dias: int):
    """Compensatorio por mora + moratorio, ambos sobre el exigible (R17)."""
    return interes(base, comp, n_dias), interes(base, morat, n_dias)
