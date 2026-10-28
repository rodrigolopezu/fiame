"""Datos de entrada y salida del simulador (contrato de la API).

Montos y tasas viajan como texto en el JSON ("57.38") para que el cliente web no los
convierta a punto flotante. Las tasas de salida van en porcentaje con 7 decimales.
"""
from datetime import date
from decimal import Decimal
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field, model_validator

from app.finanzas.tasas import Periodo, Tasa, TipoTasa

Moneda = Literal["PEN", "USD"]
Modalidad = Literal["FIN_DE_MES", "CUOTAS"]
MedioPago = Literal["EFECTIVO", "YAPE", "PLIN", "TRANSFERENCIA", "OTRO"]
Dinero = Annotated[Decimal, Field(max_digits=12, decimal_places=2)]


# ---------------------------------------------------------------- Entrada

class TasaEntrada(BaseModel):
    tipo: TipoTasa
    periodo: Periodo = Periodo.ANUAL
    valor: Decimal = Field(gt=0, max_digits=12, decimal_places=7, description="En porcentaje")
    capitalizacion: Periodo | None = Field(default=None, description="Solo si es nominal; por defecto diaria")

    @model_validator(mode="after")
    def _validar(self):
        self.a_tasa()
        return self

    def a_tasa(self) -> Tasa:
        return Tasa(self.tipo, self.periodo, self.valor, self.capitalizacion)


class Condiciones(BaseModel):
    moneda: Moneda = "PEN"
    limite_credito: Dinero = Field(gt=0)
    max_meses: int = Field(ge=1, le=36)
    dia_corte: int = Field(ge=1, le=28)
    dia_pago: int = Field(ge=1, le=28)
    tasa_compensatoria: TasaEntrada
    tasa_moratoria: TasaEntrada
    bloquear_con_vencido: bool = True


class ItemVenta(BaseModel):
    descripcion: str = Field(min_length=1, max_length=120)
    cantidad: Decimal = Field(default=Decimal("1"), gt=0, max_digits=10, decimal_places=3)
    precio_lista: Dinero = Field(gt=0)
    moneda: Moneda = "PEN"
    permite_pago_unico: bool = True
    permite_cuotas: bool = True


class EventoVenta(BaseModel):
    tipo: Literal["VENTA"] = "VENTA"
    fecha: date
    items: list[ItemVenta] = Field(min_length=1)
    modalidad: Modalidad = "FIN_DE_MES"
    numero_cuotas: int | None = Field(default=None, ge=1, le=36)
    tipo_cambio: Decimal | None = Field(default=None, gt=0, max_digits=8, decimal_places=3)


class EventoPago(BaseModel):
    tipo: Literal["PAGO"] = "PAGO"
    fecha: date
    cantidad_estados: int = Field(default=1, ge=1, description="Estados de cuenta a pagar, del más antiguo")
    medio: MedioPago = "EFECTIVO"


class EventoCambioCondiciones(BaseModel):
    tipo: Literal["CAMBIO_CONDICIONES"] = "CAMBIO_CONDICIONES"
    fecha: date
    tasa_compensatoria: TasaEntrada | None = None
    tasa_moratoria: TasaEntrada | None = None
    limite_credito: Dinero | None = Field(default=None, gt=0)


class EventoAnulacion(BaseModel):
    tipo: Literal["ANULAR_VENTA"] = "ANULAR_VENTA"
    fecha: date
    venta: int = Field(ge=1, description="Número de la venta a anular")


Evento = Annotated[
    Union[EventoVenta, EventoPago, EventoCambioCondiciones, EventoAnulacion],
    Field(discriminator="tipo"),
]


class SolicitudSimulacion(BaseModel):
    condiciones: Condiciones
    eventos: list[Evento] = []
    fecha_hasta: date = Field(description="Día hasta el que se simula; hace de 'hoy'")


# ---------------------------------------------------------------- Salida

class LineaCredito(BaseModel):
    limite: Decimal
    usado: Decimal
    disponible: Decimal


class ResumenTasa(BaseModel):
    descripcion: str
    tea: Decimal
    tem: Decimal


class RegistroBitacora(BaseModel):
    evento: int | None = Field(description="Posición del evento en la solicitud; nulo si es un corte")
    fecha: date
    tipo: str
    resultado: Literal["OK", "RECHAZADO"]
    mensaje: str
    linea: LineaCredito


class ItemVentaSalida(BaseModel):
    descripcion: str
    cantidad: Decimal
    precio_lista: Decimal
    moneda: Moneda
    subtotal: Decimal


class CuotaSalida(BaseModel):
    numero: int
    fecha_corte: date
    fecha_vencimiento: date
    saldo_inicial: Decimal
    interes: Decimal
    cuota: Decimal
    amortizacion: Decimal
    saldo_final: Decimal
    libera_linea: Decimal
    estado: Literal["PENDIENTE", "PAGADA"]
    estado_cuenta: str | None


class VentaSalida(BaseModel):
    numero: int
    evento: int
    fecha: date
    modalidad: Modalidad
    numero_cuotas: int | None
    moneda: Moneda
    tipo_cambio: Decimal | None
    items: list[ItemVentaSalida]
    capital: Decimal
    tasa_compensatoria: str
    tasa_moratoria: str
    fecha_corte: date
    fecha_pago: date
    dias: int
    tasa_periodo: Decimal
    interes: Decimal
    total: Decimal
    tem: Decimal | None
    estado: Literal["VIGENTE", "PAGADA", "ANULADA"]
    estado_cuenta: str | None
    cuotas: list[CuotaSalida]


class LineaEstadoCuenta(BaseModel):
    tipo: Literal["COMPRA", "CUOTA"]
    venta: int
    fecha: date
    descripcion: str
    cuota: str | None
    capital: Decimal
    dias: int | None
    tasa: Decimal | None
    interes: Decimal
    total: Decimal


class VencidoInformativo(BaseModel):
    codigo: str
    fecha_pago: date
    exigible: Decimal
    dias_atraso: int


class DeudaAlDia(BaseModel):
    fecha: date
    dias_mora: int
    tasa_compensatoria: Decimal
    interes_compensatorio: Decimal
    tasa_moratoria: Decimal
    interes_moratorio: Decimal
    recargo: Decimal = Field(description="Intereses por mora: compensatorio + moratorio")
    total_a_pagar: Decimal


class EstadoCuentaSalida(BaseModel):
    codigo: str
    periodo_desde: date
    fecha_corte: date
    fecha_pago: date
    moneda: Moneda
    tasa_compensatoria: str
    tea_compensatoria: Decimal
    tasa_moratoria: str
    tea_moratoria: Decimal
    lineas: list[LineaEstadoCuenta]
    total_capital: Decimal
    total_interes: Decimal
    total_a_pagar: Decimal
    linea: LineaCredito
    vencidos_anteriores: list[VencidoInformativo]
    estado: Literal["PENDIENTE", "VENCIDO", "PAGADO"]
    pagado_con: int | None
    deuda_al_dia: DeudaAlDia | None


class DetallePagoSalida(BaseModel):
    estado_cuenta: str
    fecha_pago_pactada: date
    exigible: Decimal
    dias_mora: int
    tasa_compensatoria_mora: Decimal
    interes_compensatorio_mora: Decimal
    tasa_moratoria: Decimal
    interes_moratorio: Decimal
    recargo_mora: Decimal = Field(description="Intereses por mora: compensatorio + moratorio")
    mora: Decimal
    interes: Decimal
    capital: Decimal
    total: Decimal
    libera_linea: Decimal


class PagoSalida(BaseModel):
    numero: int
    evento: int
    fecha: date
    medio: MedioPago
    detalle: list[DetallePagoSalida]
    total_mora: Decimal
    total_interes: Decimal
    total_capital: Decimal
    total: Decimal
    linea_liberada: Decimal


class ResultadoSimulacion(BaseModel):
    fecha_hasta: date
    moneda: Moneda
    tasa_compensatoria: ResumenTasa
    tasa_moratoria: ResumenTasa
    linea: LineaCredito
    bitacora: list[RegistroBitacora]
    ventas: list[VentaSalida]
    estados_cuenta: list[EstadoCuentaSalida]
    pagos: list[PagoSalida]
