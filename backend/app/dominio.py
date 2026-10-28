"""Reglas de negocio del crédito, comunes al simulador y a la aplicación.

No conoce la base de datos ni HTTP: recibe valores y devuelve resultados calculados.
Implementa los algoritmos de docs/informe/07-algoritmo.md con el núcleo de `finanzas`.
"""
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from app.finanzas.cronograma import capitalizar, cronograma_frances, liberacion_de_linea
from app.finanzas.fechas import calcular_ciclo, dias_entre, fecha_pago_del_corte, sumar_meses
from app.finanzas.mora import intereses_por_mora
from app.finanzas.redondeo import r2
from app.finanzas.tasas import Tasa

CERO = Decimal("0.00")


class ReglaDeNegocio(Exception):
    """Operación rechazada por una regla de negocio. El mensaje se muestra al usuario."""


def simbolo(moneda: str) -> str:
    return "S/" if moneda == "PEN" else "US$"


def fmt(monto: Decimal, moneda: str) -> str:
    return f"{simbolo(moneda)} {monto:,.2f}"


# ---------------------------------------------------------------- Ventas

def convertir(importe: Decimal, moneda_origen: str, moneda_destino: str, tipo_cambio: Decimal | None,
              descripcion: str = "El producto") -> Decimal:
    """Subtotal en la moneda del cliente. El tipo de cambio está en soles por dólar."""
    if moneda_origen == moneda_destino:
        return r2(importe)
    if tipo_cambio is None:
        raise ReglaDeNegocio(f"'{descripcion}' está en {moneda_origen}: se requiere el tipo de cambio")
    return r2(importe * tipo_cambio) if moneda_origen == "USD" else r2(importe / tipo_cambio)


def validar_venta(*, modalidad: str, numero_cuotas: int | None, max_meses: int,
                  todos_pago_unico: bool, todos_cuotas: bool, capital: Decimal, disponible: Decimal,
                  moneda: str, vencidos: list[str], bloquear_con_vencido: bool):
    """Validaciones de RegistrarVenta (7.4) en el orden del algoritmo."""
    if bloquear_con_vencido and vencidos:
        raise ReglaDeNegocio(f"El cliente tiene estados de cuenta vencidos: {', '.join(vencidos)}")
    if capital > disponible:
        raise ReglaDeNegocio(f"El capital {fmt(capital, moneda)} excede el crédito disponible {fmt(disponible, moneda)}")
    if modalidad == "FIN_DE_MES" and not todos_pago_unico:
        raise ReglaDeNegocio("Algún producto no permite el pago único a fin de mes")
    if modalidad == "CUOTAS":
        if not todos_cuotas:
            raise ReglaDeNegocio("Algún producto no permite el pago en cuotas")
        if numero_cuotas is None or not 1 <= numero_cuotas <= max_meses:
            raise ReglaDeNegocio(f"El número de cuotas debe estar entre 1 y {max_meses}")


@dataclass
class CuotaCalculada:
    numero: int
    fecha_corte: date
    fecha_vencimiento: date
    saldo_inicial: Decimal
    interes: Decimal
    cuota: Decimal
    amortizacion: Decimal
    saldo_final: Decimal
    libera_linea: Decimal


@dataclass
class VentaCalculada:
    fecha_corte: date
    fecha_pago: date
    dias: int
    tasa_periodo: Decimal
    interes: Decimal
    total: Decimal
    tem: Decimal | None = None
    cuotas: list[CuotaCalculada] = field(default_factory=list)


def calcular_venta(capital: Decimal, tasa: Tasa, fecha: date, dia_corte: int, dia_pago: int,
                   modalidad: str, numero_cuotas: int | None = None) -> VentaCalculada:
    """Ciclo, interés a fin de mes o cronograma con gracia (7.4 y 7.5)."""
    corte, pago = calcular_ciclo(fecha, dia_corte, dia_pago)
    dias = dias_entre(fecha, pago)
    tasa_periodo = tasa.efectiva(dias)
    if modalidad == "FIN_DE_MES":
        interes = r2(capital * tasa_periodo)
        return VentaCalculada(corte, pago, dias, tasa_periodo, interes, capital + interes)

    total = capitalizar(capital, tasa_periodo)
    tem = tasa.tem()
    filas = cronograma_frances(total, tem, numero_cuotas)
    liberaciones = liberacion_de_linea(capital, [f.amortizacion for f in filas])
    cuotas = []
    for fila, libera in zip(filas, liberaciones):
        corte_k = sumar_meses(corte, fila.numero)
        cuotas.append(CuotaCalculada(
            numero=fila.numero, fecha_corte=corte_k, fecha_vencimiento=fecha_pago_del_corte(corte_k, dia_pago),
            saldo_inicial=fila.saldo_inicial, interes=fila.interes, cuota=fila.cuota,
            amortizacion=fila.amortizacion, saldo_final=fila.saldo_final, libera_linea=libera,
        ))
    return VentaCalculada(corte, pago, dias, tasa_periodo, total - capital, total, tem, cuotas)


# ---------------------------------------------------------------- Pagos

@dataclass
class Liquidacion:
    """Monto a pagar de un estado de cuenta en una fecha, con su desglose (7.7)."""
    exigible: Decimal
    dias_mora: int
    tasa_compensatoria_mora: Decimal
    interes_compensatorio_mora: Decimal
    tasa_moratoria: Decimal
    interes_moratorio: Decimal
    mora: Decimal
    interes: Decimal
    capital: Decimal
    total: Decimal


def liquidar(capital: Decimal, interes: Decimal, compensatoria: Tasa, moratoria: Tasa,
             fecha_pago_pactada: date, fecha_pago: date) -> Liquidacion:
    """Exigible + intereses por mora; desglose mora → interés compensatorio → capital (R5)."""
    exigible = capital + interes
    dias_mora = max(0, dias_entre(fecha_pago_pactada, fecha_pago))
    m = intereses_por_mora(exigible, compensatoria, moratoria, dias_mora)
    return Liquidacion(
        exigible=exigible, dias_mora=dias_mora,
        tasa_compensatoria_mora=m.tasa_compensatoria, interes_compensatorio_mora=m.interes_compensatorio,
        tasa_moratoria=m.tasa_moratoria, interes_moratorio=m.interes_moratorio,
        mora=m.interes_moratorio, interes=interes + m.interes_compensatorio, capital=capital,
        total=exigible + m.total,
    )


# ---------------------------------------------------------------- Score

@dataclass
class HistorialEstado:
    """Lo que el score necesita saber de cada estado de cuenta con deuda."""
    fecha_pago: date
    pagado_el: date | None


@dataclass
class Score:
    puntaje: int
    semaforo: str  # VERDE | AMARILLO | ROJO | SIN_HISTORIAL
    detalle: dict


def calcular_score(historial: list[HistorialEstado], hoy: date, uso_linea: Decimal) -> Score:
    """Score crediticio privado de 0 a 100 (docs/funcionamiento.md).

    - Puntualidad (50): proporción de estados de cuenta pagados a tiempo.
    - Días de mora promedio (20): 0 días = 20 puntos; 30 días o más = 0.
    - Deuda vencida hoy (20): 20 si no tiene ningún estado de cuenta vencido.
    - Uso de la línea (10): hasta 50 % = 10; hasta 80 % = 5; más = 0.
    """
    exigibles = [h for h in historial if h.pagado_el or h.fecha_pago < hoy]
    if not exigibles:
        return Score(70, "SIN_HISTORIAL", {"mensaje": "Todavía no tiene pagos exigibles"})
    atrasos = [max(0, dias_entre(h.fecha_pago, h.pagado_el or hoy)) for h in exigibles]
    a_tiempo = sum(1 for a in atrasos if a == 0)
    puntualidad = round(50 * a_tiempo / len(exigibles))
    promedio = sum(atrasos) / len(atrasos)
    mora = round(20 * max(0.0, 1 - promedio / 30))
    vencidos = sum(1 for h in exigibles if h.pagado_el is None)
    deuda = 0 if vencidos else 20
    uso = 10 if uso_linea <= Decimal("0.5") else 5 if uso_linea <= Decimal("0.8") else 0
    puntaje = puntualidad + mora + deuda + uso
    semaforo = "VERDE" if puntaje >= 70 else "AMARILLO" if puntaje >= 40 else "ROJO"
    return Score(puntaje, semaforo, {
        "puntualidad": puntualidad, "mora_promedio": mora, "deuda_vencida": deuda, "uso_linea": uso,
        "pagos_a_tiempo": a_tiempo, "estados_exigibles": len(exigibles),
        "dias_mora_promedio": round(promedio, 1), "estados_vencidos": vencidos,
    })
