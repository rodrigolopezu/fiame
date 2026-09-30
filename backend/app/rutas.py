"""Endpoints de la API."""
from datetime import date
from decimal import Decimal

from fastapi import APIRouter
from pydantic import BaseModel, Field, model_validator

from app.finanzas.cronograma import capitalizar, cronograma_frances
from app.finanzas.fechas import calcular_ciclo, dias_entre
from app.finanzas.mora import interes, intereses_por_mora
from app.finanzas.redondeo import a_porcentaje
from app.finanzas.tasas import Periodo, nominal_equivalente
from app.simulador import esquemas as e
from app.simulador.motor import simular

router = APIRouter(prefix="/api")


@router.get("/salud")
def salud():
    return {"estado": "ok"}


@router.post("/simular", response_model=e.ResultadoSimulacion)
def simular_credito(solicitud: e.SolicitudSimulacion):
    """Simula el crédito de un cliente con sus ventas, cortes y pagos hasta `fecha_hasta`."""
    return simular(solicitud)


# ---------------------------------------------------------------- Calculadoras

class NominalBuscada(BaseModel):
    periodo: Periodo
    capitalizacion: Periodo = Periodo.DIARIA


class RespuestaTasa(BaseModel):
    descripcion: str
    dias: int
    tasa_efectiva: Decimal
    tea: Decimal
    tem: Decimal
    ted: Decimal
    nominal: Decimal | None


class SolicitudTasa(BaseModel):
    tasa: e.TasaEntrada
    dias: int = Field(default=30, ge=1, description="Días de la tasa efectiva buscada")
    nominal: NominalBuscada | None = None


@router.post("/calculadora/tasa", response_model=RespuestaTasa)
def convertir_tasa(s: SolicitudTasa):
    """Convierte una tasa a su efectiva de N días, TEA, TEM y, si se pide, a una nominal."""
    tasa = s.tasa.a_tasa()
    respuesta = {
        "descripcion": tasa.descripcion(),
        "dias": s.dias,
        "tasa_efectiva": a_porcentaje(tasa.efectiva(s.dias)),
        "tea": a_porcentaje(tasa.tea()),
        "tem": a_porcentaje(tasa.tem()),
        "ted": a_porcentaje(tasa.efectiva(1)),
        "nominal": None,
    }
    if s.nominal:
        respuesta["nominal"] = a_porcentaje(nominal_equivalente(
            tasa.efectiva(s.nominal.periodo.dias), s.nominal.periodo.dias,
            s.nominal.periodo, s.nominal.capitalizacion))
    return respuesta


class SolicitudInteres(BaseModel):
    capital: e.Dinero = Field(gt=0)
    tasa: e.TasaEntrada
    fecha_inicio: date | None = None
    fecha_fin: date | None = None
    dias: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _plazo(self):
        if self.dias is None and not (self.fecha_inicio and self.fecha_fin):
            raise ValueError("Indique los días o las fechas de inicio y fin")
        return self


class RespuestaInteres(BaseModel):
    dias: int
    tasa_efectiva: Decimal
    interes: Decimal
    valor_futuro: Decimal


@router.post("/calculadora/interes", response_model=RespuestaInteres)
def calcular_interes(s: SolicitudInteres):
    """Interés y valor futuro de un capital por días calendario exactos."""
    dias = s.dias if s.dias is not None else dias_entre(s.fecha_inicio, s.fecha_fin)
    tasa = s.tasa.a_tasa()
    i = interes(s.capital, tasa, dias)
    return {"dias": dias, "tasa_efectiva": a_porcentaje(tasa.efectiva(dias)), "interes": i,
            "valor_futuro": s.capital + i}


class SolicitudCronograma(BaseModel):
    capital: e.Dinero = Field(gt=0)
    tasa: e.TasaEntrada
    numero_cuotas: int = Field(ge=1, le=480)
    dias_periodo: int = Field(default=30, ge=1, description="Días entre cuotas")
    dias_gracia: int = Field(default=0, ge=0, description="Días de gracia total antes de la primera cuota")


class FilaSalida(BaseModel):
    numero: int
    saldo_inicial: Decimal
    interes: Decimal
    cuota: Decimal
    amortizacion: Decimal
    saldo_final: Decimal


class RespuestaCronograma(BaseModel):
    tasa_gracia: Decimal
    capital_financiado: Decimal
    tasa_periodo: Decimal
    filas: list[FilaSalida]
    total_interes: Decimal
    total_pagado: Decimal


@router.post("/calculadora/cronograma", response_model=RespuestaCronograma)
def calcular_cronograma(s: SolicitudCronograma):
    """Cronograma por el método francés vencido ordinario, con gracia total opcional."""
    tasa = s.tasa.a_tasa()
    tasa_gracia = tasa.efectiva(s.dias_gracia) if s.dias_gracia else Decimal("0")
    capital = capitalizar(s.capital, tasa_gracia) if s.dias_gracia else s.capital
    tep = tasa.efectiva(s.dias_periodo)
    filas = cronograma_frances(capital, tep, s.numero_cuotas)
    return {
        "tasa_gracia": a_porcentaje(tasa_gracia), "capital_financiado": capital,
        "tasa_periodo": a_porcentaje(tep), "filas": [FilaSalida(**vars(f)) for f in filas],
        "total_interes": sum((f.interes for f in filas), Decimal("0.00")),
        "total_pagado": sum((f.cuota for f in filas), Decimal("0.00")),
    }


class SolicitudMora(BaseModel):
    exigible: e.Dinero = Field(gt=0)
    tasa_compensatoria: e.TasaEntrada
    tasa_moratoria: e.TasaEntrada
    dias_mora: int = Field(ge=0)


class RespuestaMora(BaseModel):
    dias_mora: int
    tasa_compensatoria: Decimal
    interes_compensatorio: Decimal
    tasa_moratoria: Decimal
    interes_moratorio: Decimal
    total_a_pagar: Decimal


@router.post("/calculadora/mora", response_model=RespuestaMora)
def calcular_mora(s: SolicitudMora):
    """Interés compensatorio y moratorio por días de atraso, ambos sobre el exigible."""
    m = intereses_por_mora(s.exigible, s.tasa_compensatoria.a_tasa(), s.tasa_moratoria.a_tasa(), s.dias_mora)
    return {
        "dias_mora": m.dias, "tasa_compensatoria": a_porcentaje(m.tasa_compensatoria),
        "interes_compensatorio": m.interes_compensatorio, "tasa_moratoria": a_porcentaje(m.tasa_moratoria),
        "interes_moratorio": m.interes_moratorio, "total_a_pagar": s.exigible + m.total,
    }


class SolicitudCiclo(BaseModel):
    fecha_compra: date
    dia_corte: int = Field(ge=1, le=28)
    dia_pago: int = Field(ge=1, le=28)


class RespuestaCiclo(BaseModel):
    fecha_corte: date
    fecha_pago: date
    dias_hasta_pago: int


@router.post("/calculadora/ciclo", response_model=RespuestaCiclo)
def calcular_ciclo_compra(s: SolicitudCiclo):
    """Fecha de corte y de pago del ciclo en que cae una compra."""
    corte, pago = calcular_ciclo(s.fecha_compra, s.dia_corte, s.dia_pago)
    return {"fecha_corte": corte, "fecha_pago": pago, "dias_hasta_pago": dias_entre(s.fecha_compra, pago)}
