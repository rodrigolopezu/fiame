"""Verificación contra los ejercicios resueltos del libro del curso.

Martín Senmache, J. M. (2025). Matemática Financiera (5.ª ed.). El código del caso es el
número del ejercicio en el libro.

- Dinero: debe coincidir al céntimo (2 decimales).
- Tasas: se comparan a 7 decimales en porcentaje. Si el libro imprime más o menos
  decimales, se acepta la diferencia que se explica solo por redondear en distinto punto.
"""
from datetime import date
from decimal import ROUND_HALF_UP, Decimal as D, localcontext

import pytest

from app.finanzas.cronograma import capitalizar, cuota_francesa
from app.finanzas.fechas import dias_entre
from app.finanzas.mora import interes, intereses_por_mora
from app.finanzas.redondeo import a_porcentaje
from app.finanzas.tasas import Periodo as P, Tasa, TipoTasa, nominal_equivalente

E, N = TipoTasa.EFECTIVA, TipoTasa.NOMINAL
SIETE = D("0.0000001")


def coincide_redondeando(nuestra: D, libro: str) -> bool:
    """¿Existe un valor que redondeado a 7 decimales dé `nuestra` y al número de decimales
    del libro dé `libro`? Es decir, ambas cifras son redondeos del mismo número."""
    decimales = len(libro.split(".")[1]) if "." in libro else 0
    medio_libro = D(1).scaleb(-decimales) / 2
    medio_nuestro = SIETE / 2
    b = D(libro)
    return nuestra - medio_nuestro <= b + medio_libro and b - medio_libro <= nuestra + medio_nuestro


# (ejercicio, tasa dada, días de la tasa buscada, respuesta del libro en %)
CONVERSIONES = [
    ("3-51 TEM", Tasa(N, P.ANUAL, D("12"), P.MENSUAL), 30, "1.000"),
    ("3-51 TET", Tasa(N, P.ANUAL, D("12"), P.MENSUAL), 90, "3.0301"),
    ("3-51 TEA", Tasa(N, P.ANUAL, D("12"), P.MENSUAL), 360, "12.682503"),
    ("3-52a", Tasa(N, P.ANUAL, D("18.75"), P.MENSUAL), 360, "20.448277"),
    ("3-52b", Tasa(N, P.ANUAL, D("16.98"), P.TRIMESTRAL), 360, "18.0921242"),
    ("3-52c", Tasa(N, P.ANUAL, D("17.23"), P.SEMESTRAL), 360, "17.9721822"),
    ("3-52d", Tasa(N, P.ANUAL, D("20"), P.ANUAL), 360, "20.0"),
    ("4-9", Tasa(N, P.ANUAL, D("24"), P.QUINCENAL), 360, "26.97346485"),
    ("4-10", Tasa(N, P.ANUAL, D("28"), P.DIARIA), 30, "2.359840157"),
    ("4-11", Tasa(N, P.SEMESTRAL, D("4")), 30, "0.66881927"),
    ("4-12", Tasa(N, P.CUATRIMESTRAL, D("3")), 30, "0.752725104"),
    ("4-13", Tasa(E, P.MENSUAL, D("0.89")), 360, "11.21861036"),
    ("4-14", Tasa(E, P.ANUAL, D("12")), 30, "0.9488793"),
    ("4-15", Tasa(E, P.ANUAL, D("32")), 60, "4.7359208"),
    ("4-16", Tasa(E, P.MENSUAL, D("0.99")), 360, "12.5486957"),
    ("4-17", Tasa(E, P.MENSUAL, D("3.9")), 180, "25.80366265"),
    ("4-21", Tasa(E, P.MENSUAL, D("4.5")), 360, "69.5881433"),
    ("4-24 TES", Tasa(N, P.TRIMESTRAL, D("1")), 180, "2.02002"),
]


@pytest.mark.parametrize("ejercicio, tasa, dias, libro", CONVERSIONES, ids=[c[0] for c in CONVERSIONES])
def test_conversion_de_tasas(ejercicio, tasa, dias, libro):
    assert coincide_redondeando(a_porcentaje(tasa.efectiva(dias)), libro)


# (ejercicio, TEP dada, días de la TEP, periodo de la nominal, capitalización, libro en %)
NOMINALES = [
    ("4-3", D("0.08"), 30, P.ANUAL, P.MENSUAL, "96"),
    ("4-8", D("0.12"), 360, P.TRIMESTRAL, P.QUINCENAL, "2.83991694"),
    ("4-19", D("0.045"), 30, P.ANUAL, P.QUINCENAL, "53.40579602"),
    ("4-20", D("0.081"), 30, P.SEMESTRAL, P.QUINCENAL, "47.65379813"),
    ("4-22b", D("0.03"), 90, P.ANUAL, P.MENSUAL, "11.88196085"),
]


@pytest.mark.parametrize("ejercicio, tep, dias, periodo, cap, libro", NOMINALES, ids=[c[0] for c in NOMINALES])
def test_efectiva_a_nominal(ejercicio, tep, dias, periodo, cap, libro):
    assert coincide_redondeando(a_porcentaje(nominal_equivalente(tep, dias, periodo, cap)), libro)


def exacto(expresion) -> D:
    """Valor exacto (50 dígitos) en %, redondeado half-up a 7 decimales."""
    with localcontext() as ctx:
        ctx.prec = 50
        return (expresion() * 100).quantize(SIETE, ROUND_HALF_UP)


# Casos donde el libro difiere en el 7.° decimal o más allá. Se verifica que nuestro
# valor es el exacto de la fórmula directa, y cuánto difiere del libro.
# (ejercicio, nuestra tasa, fórmula exacta, libro en %, diferencia máxima; None = errata)
DIFERENCIAS_DOCUMENTADAS = [
    # El libro deriva la TEA de la TES ya redondeada (2.02002 %): paso intermedio (R12).
    ("4-24 TEA", lambda: Tasa(N, P.TRIMESTRAL, D("1")).efectiva(360),
     lambda: (1 + D("0.01") / 90) ** 360 - 1, "4.080844807", D("0.0000014")),
    # Errores de tipeo del libro: la misma tasa en el ej. 4-24 da nuestro valor.
    ("4-23 TET", lambda: Tasa(N, P.ANUAL, D("4")).efectiva(90),
     lambda: (1 + D("0.04") / 360) ** 90 - 1, "1.004966666", None),
    ("4-23 TES", lambda: Tasa(N, P.ANUAL, D("4")).efectiva(180),
     lambda: (1 + D("0.04") / 360) ** 180 - 1, "2.02003298", None),
    # Redondeos intermedios del libro (diferencias de 2e-7 puntos porcentuales o menos).
    ("4-22a", lambda: Tasa(N, P.BIMESTRAL, D("2")).efectiva(360),
     lambda: (1 + D("0.02") / 60) ** 360 - 1, "12.74743055", D("0.0000002")),
    ("4-4", lambda: nominal_equivalente(D("0.042"), 180, P.ANUAL, P.DIARIA),
     lambda: 360 * (D("1.042") ** (D(1) / 180) - 1), "8.22932892", D("0.0000002")),
    ("4-7", lambda: nominal_equivalente(D("0.0175"), 30, P.MENSUAL, P.DIARIA),
     lambda: 30 * (D("1.0175") ** (D(1) / 30) - 1), "1.73536554", D("0.0000001")),
]


@pytest.mark.parametrize("ejercicio, nuestra, formula, libro, diferencia", DIFERENCIAS_DOCUMENTADAS,
                         ids=[c[0] for c in DIFERENCIAS_DOCUMENTADAS])
def test_diferencias_documentadas(ejercicio, nuestra, formula, libro, diferencia):
    valor = a_porcentaje(nuestra())
    assert valor == exacto(formula)
    if diferencia is not None:
        assert abs(valor - D(libro)) <= diferencia


def valor_futuro(capital: D, tasa: Tasa, dias: int) -> D:
    return capital + interes(capital, tasa, dias)


@pytest.mark.parametrize("ejercicio, calculado, libro", [
    ("3-1", lambda: valor_futuro(D("50000"), Tasa(N, P.MENSUAL, D("2")), 900), "91087.73"),
    ("3-2", lambda: valor_futuro(D("130000"), Tasa(N, P.ANUAL, D("2.4"), P.MENSUAL), 720), "136385.65"),
    ("3-3", lambda: valor_futuro(D("3000"), Tasa(N, P.ANUAL, D("18.5")),
                                 dias_entre(date(2010, 2, 14), date(2011, 9, 13))), "4033.10"),
    ("4-23", lambda: valor_futuro(D("60000"), Tasa(N, P.ANUAL, D("4")), 90), "60602.98"),
    ("4-24", lambda: valor_futuro(D("200000"), Tasa(N, P.TRIMESTRAL, D("1")), 180), "204040.04"),
], ids=["3-1", "3-2", "3-3", "4-23", "4-24"])
def test_valor_futuro(ejercicio, calculado, libro):
    assert calculado() == D(libro)


def test_dias_calendario_exactos_ej_3_3():
    assert dias_entre(date(2010, 2, 14), date(2011, 9, 13)) == 576


@pytest.mark.parametrize("ejercicio, vn, comp, morat, dias, otros, libro, ic, im", [
    # Pagaré con 7 días de atraso: + comisión 50, gastos 15, portes 5.
    ("5-36c", "20000", Tasa(N, P.ANUAL, D("20")), Tasa(E, P.ANUAL, D("60")), 7, "70",
     "20331.53", "77.91", "183.62"),
    # 6 días de atraso: + gastos 20, portes 7, pago tardío 80, − retención 6,585.
    ("5-37e", "65850", Tasa(E, P.ANUAL, D("24")), Tasa(N, P.ANUAL, D("12")), 6, "-6478",
     "59740.32", None, None),
    ("5-39c", "15000", Tasa(E, P.ANUAL, D("10.2")), Tasa(E, P.ANUAL, D("3.52")), 3, "0",
     "15016.47", None, None),
    # 6 días de atraso: + cobranza 50, portes 2, gastos 15, − retención 7,500.
    ("5-40c", "150000", Tasa(E, P.ANUAL, D("12.7")), Tasa(N, P.ANUAL, D("5")), 6, "-7433",
     "142991.24", None, None),
], ids=["5-36c", "5-37e", "5-39c", "5-40c"])
def test_intereses_por_mora(ejercicio, vn, comp, morat, dias, otros, libro, ic, im):
    m = intereses_por_mora(D(vn), comp, morat, dias)
    assert D(vn) + m.total + D(otros) == D(libro)
    if ic:
        assert (m.interes_compensatorio, m.interes_moratorio) == (D(ic), D(im))


def cuota(capital: str, tasa: Tasa, dias_periodo: int, n: int) -> D:
    return cuota_francesa(D(capital), tasa.efectiva(dias_periodo), n)


def cuota_con_gracia(capital: str, tasa: Tasa, dias_periodo: int, periodos_gracia: int, n: int) -> D:
    capitalizado = capitalizar(D(capital), tasa.efectiva(dias_periodo * periodos_gracia))
    return cuota_francesa(capitalizado, tasa.efectiva(dias_periodo), n)


@pytest.mark.parametrize("ejercicio, calculado, libro", [
    ("7-1", lambda: cuota("33759.20", Tasa(E, P.ANUAL, D("7.5")), 30, 36), "1046.31"),
    ("7-2", lambda: cuota("2890", Tasa(E, P.ANUAL, D("21.7")), 120, 9), "439.16"),
    ("7-3", lambda: cuota("250000", Tasa(E, P.ANUAL, D("12")), 90, 16), "19711.09"),
    ("7-5", lambda: cuota("8279.10", Tasa(E, P.ANUAL, D("19.9")), 60, 24), "492.61"),
    ("7-6", lambda: cuota("32800", Tasa(N, P.SEMESTRAL, D("8.4")), 60, 15), "2715.63"),
    ("7-13a", lambda: cuota("4499.10", Tasa(E, P.MENSUAL, D("2.99")), 30, 36), "205.77"),
    ("7-13b", lambda: cuota_con_gracia("4499.10", Tasa(E, P.MENSUAL, D("2.99")), 30, 6, 36), "245.56"),
    ("7-14a", lambda: cuota("36000", Tasa(E, P.ANUAL, D("8.5")), 180, 10), "4474.64"),
    ("7-14c", lambda: cuota_con_gracia("36000", Tasa(E, P.ANUAL, D("8.5")), 180, 1, 9), "5080.93"),
    ("7-16a", lambda: cuota("46400", Tasa(E, P.ANUAL, D("7.9")), 30, 48), "1124.67"),
    ("7-17a", lambda: cuota("3869.10", Tasa(E, P.ANUAL, D("17")), 30, 12), "350.69"),
    ("7-17b", lambda: cuota_con_gracia("3869.10", Tasa(E, P.ANUAL, D("17")), 30, 3, 9), "477.06"),
    ("8-1", lambda: cuota("112000", Tasa(E, P.ANUAL, D("10")), 120, 9), "14537.95"),
    ("8-3", lambda: cuota("80000", Tasa(E, P.ANUAL, D("9")), 180, 8), "12080.78"),
], ids=["7-1", "7-2", "7-3", "7-5", "7-6", "7-13a", "7-13b", "7-14a", "7-14c", "7-16a",
        "7-17a", "7-17b", "8-1", "8-3"])
def test_cuota_metodo_frances(ejercicio, calculado, libro):
    assert calculado() == D(libro)
