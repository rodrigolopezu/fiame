"""Convierte las filas de la base de datos en las respuestas de la API.

Ventas, estados de cuenta y pagos usan el mismo formato que el simulador, para que la
interfaz reutilice sus componentes.
"""
from datetime import date
from decimal import Decimal

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import modelos as m
from app.dominio import CERO, calcular_score, HistorialEstado, liquidar
from app.finanzas.redondeo import a_porcentaje
from app.simulador import esquemas as e
from app.servicios import credito
from app.servicios.clientes import uso_de_linea


# ---------------------------------------------------------------- Esquemas propios

class TasaVista(BaseModel):
    tipo: str
    periodo: str
    valor: Decimal
    capitalizacion: str | None
    descripcion: str
    tea: Decimal


class ScoreVista(BaseModel):
    puntaje: int
    semaforo: str
    detalle: dict


class VentaVista(e.VentaSalida):
    cliente_id: int
    cliente: str


class EstadoCuentaVista(e.EstadoCuentaSalida):
    id: int
    cliente_id: int
    cliente: str


class PagoVista(e.PagoSalida):
    cliente_id: int
    cliente: str
    moneda: str
    estado: str
    motivo_anulacion: str | None


class ClienteResumen(BaseModel):
    id: int
    nombre: str
    tipo_documento: str
    numero_documento: str
    telefono: str | None
    moneda: str
    estado: str
    linea: e.LineaCredito
    deuda_pendiente: Decimal
    deuda_al_dia: Decimal
    estados_vencidos: int
    proximo_vencimiento: date | None
    score: ScoreVista
    tiene_codigo: bool


class ClienteDetalle(ClienteResumen):
    nombres: str
    apellidos: str
    email: str | None
    direccion: str | None
    limite_credito: Decimal
    max_meses: int
    dia_corte: int
    dia_pago: int
    fecha_alta: date
    tasa_compensatoria: TasaVista
    tasa_moratoria: TasaVista
    puede_cambiar_ciclo: bool
    ventas: list[VentaVista]
    estados_cuenta: list[EstadoCuentaVista]
    pagos: list[PagoVista]


# ---------------------------------------------------------------- Conversores

def tasa_vista(t: m.Tasa) -> TasaVista:
    d = t.a_dominio()
    return TasaVista(tipo=t.tipo, periodo=t.periodo, valor=t.valor.normalize(), capitalizacion=t.capitalizacion,
                     descripcion=d.descripcion(), tea=a_porcentaje(t.tea))


def venta_vista(v: m.Venta, cliente: m.Cliente) -> VentaVista:
    def codigo(corte: date) -> str | None:
        ec = credito.estado_cuenta_de(cliente, corte)
        return ec.codigo if ec else None

    return VentaVista(
        numero=v.id or 0, evento=0, fecha=v.fecha, modalidad=v.modalidad, numero_cuotas=v.numero_cuotas,
        moneda=v.moneda, tipo_cambio=v.tipo_cambio,
        items=[e.ItemVentaSalida(descripcion=d.descripcion, cantidad=d.cantidad.normalize(),
                                 precio_lista=d.precio_lista, moneda=d.moneda_producto, subtotal=d.subtotal)
               for d in v.detalle],
        capital=v.capital, tasa_compensatoria=v.tasa_compensatoria.a_dominio().descripcion(),
        tasa_moratoria=v.tasa_moratoria.a_dominio().descripcion(), fecha_corte=v.fecha_corte,
        fecha_pago=v.fecha_pago, dias=v.dias, tasa_periodo=a_porcentaje(v.tasa_periodo), interes=v.interes,
        total=v.total, tem=a_porcentaje(v.tem) if v.tem is not None else None, estado=v.estado,
        estado_cuenta=codigo(v.fecha_corte) if v.modalidad == "FIN_DE_MES" and v.id else None,
        cuotas=[
            e.CuotaSalida(numero=c.numero, fecha_corte=c.fecha_corte, fecha_vencimiento=c.fecha_vencimiento,
                          saldo_inicial=c.saldo_inicial, interes=c.interes, cuota=c.monto,
                          amortizacion=c.amortizacion, saldo_final=c.saldo_final, libera_linea=c.libera_linea,
                          estado=c.estado, estado_cuenta=codigo(c.fecha_corte) if v.id else None)
            for c in v.cuotas
        ],
        cliente_id=cliente.id, cliente=cliente.nombre_completo,
    )


def _pago_de(s: Session, ec: m.EstadoCuenta) -> m.Pago | None:
    for p in credito.pagos_del_cliente(s, ec.cliente, solo_validos=True):
        if any(d.estado_cuenta_id == ec.id for d in p.detalle):
            return p
    return None


def estado_cuenta_vista(s: Session, ec: m.EstadoCuenta, hoy: date) -> EstadoCuentaVista:
    cliente = ec.cliente
    estado, deuda = ec.estado, None
    if ec.estado == "PENDIENTE" and hoy > ec.fecha_pago:
        estado = "VENCIDO"
        liq = liquidar(ec.total_capital, ec.total_interes, ec.tasa_compensatoria.a_dominio(),
                       ec.tasa_moratoria.a_dominio(), ec.fecha_pago, hoy)
        deuda = e.DeudaAlDia(
            fecha=hoy, dias_mora=liq.dias_mora, tasa_compensatoria=a_porcentaje(liq.tasa_compensatoria_mora),
            interes_compensatorio=liq.interes_compensatorio_mora, tasa_moratoria=a_porcentaje(liq.tasa_moratoria),
            interes_moratorio=liq.interes_moratorio, recargo=liq.total - liq.exigible, total_a_pagar=liq.total)

    # Informativo: estados anteriores que al momento del corte seguían vencidos.
    anteriores = []
    for otro in cliente.estados_cuenta:
        if otro.fecha_pago >= ec.fecha_corte or otro.total_a_pagar == 0:
            continue
        pago = _pago_de(s, otro)
        if pago is None or pago.fecha_pago > ec.fecha_corte:
            anteriores.append(e.VencidoInformativo(
                codigo=otro.codigo, fecha_pago=otro.fecha_pago, exigible=otro.total_a_pagar,
                dias_atraso=(ec.fecha_corte - otro.fecha_pago).days))

    pago = _pago_de(s, ec)
    comp, mor = ec.tasa_compensatoria, ec.tasa_moratoria
    return EstadoCuentaVista(
        id=ec.id, cliente_id=cliente.id, cliente=cliente.nombre_completo, codigo=ec.codigo,
        periodo_desde=ec.periodo_desde, fecha_corte=ec.fecha_corte, fecha_pago=ec.fecha_pago, moneda=ec.moneda,
        tasa_compensatoria=comp.a_dominio().descripcion(), tea_compensatoria=a_porcentaje(comp.tea),
        tasa_moratoria=mor.a_dominio().descripcion(), tea_moratoria=a_porcentaje(mor.tea),
        lineas=[
            e.LineaEstadoCuenta(
                tipo=l.tipo, venta=l.venta.id, fecha=l.venta.fecha, descripcion=l.venta.descripcion,
                cuota=f"{l.cuota.numero}/{l.venta.numero_cuotas}" if l.cuota else None, capital=l.capital,
                dias=None if l.cuota else l.venta.dias,
                tasa=a_porcentaje(l.venta.tem if l.cuota else l.venta.tasa_periodo),
                interes=l.interes, total=l.total)
            for l in credito.lineas_del_corte(cliente, ec.fecha_corte)
        ],
        total_capital=ec.total_capital, total_interes=ec.total_interes, total_a_pagar=ec.total_a_pagar,
        linea=e.LineaCredito(limite=ec.limite_credito, usado=ec.credito_usado, disponible=ec.credito_disponible),
        vencidos_anteriores=anteriores, estado=estado, pagado_con=pago.id if pago else None, deuda_al_dia=deuda,
    )


def pago_vista(p: m.Pago) -> PagoVista:
    cliente = credito.cliente_del_pago(p)
    return PagoVista(
        numero=p.id, evento=0, fecha=p.fecha_pago, medio=p.medio,
        detalle=[
            e.DetallePagoSalida(
                estado_cuenta=d.estado_cuenta.codigo, fecha_pago_pactada=d.estado_cuenta.fecha_pago,
                exigible=d.exigible, dias_mora=d.dias_mora,
                tasa_compensatoria_mora=a_porcentaje(d.tasa_compensatoria_mora),
                interes_compensatorio_mora=d.interes_compensatorio_mora,
                tasa_moratoria=a_porcentaje(d.tasa_moratoria), interes_moratorio=d.interes_moratorio,
                recargo_mora=d.total - d.exigible, mora=d.interes_moratorio, interes=d.interes, capital=d.capital, total=d.total,
                libera_linea=sum((l.libera_linea for l in credito.lineas_del_corte(cliente, d.estado_cuenta.fecha_corte)), CERO),
            )
            for d in p.detalle
        ],
        total_mora=p.total_mora, total_interes=p.total_interes, total_capital=p.total_capital, total=p.total,
        linea_liberada=p.linea_liberada, cliente_id=cliente.id, cliente=cliente.nombre_completo,
        moneda=cliente.moneda,
        estado=p.estado, motivo_anulacion=p.motivo_anulacion,
    )


def score_de(s: Session, cliente: m.Cliente, hoy: date, usado: Decimal) -> ScoreVista:
    historial = []
    for ec in cliente.estados_cuenta:
        if ec.total_a_pagar == 0:
            continue
        pago = _pago_de(s, ec)
        historial.append(HistorialEstado(ec.fecha_pago, pago.fecha_pago if pago else None))
    sc = calcular_score(historial, hoy, uso_de_linea(usado, cliente.limite_credito))
    return ScoreVista(puntaje=sc.puntaje, semaforo=sc.semaforo, detalle=sc.detalle)


def _resumen_campos(s: Session, cliente: m.Cliente, hoy: date) -> dict:
    usado = credito.credito_usado(s, cliente)
    pend = credito.pendientes(cliente)
    deuda_al_dia = CERO
    for ec in pend:
        liq = liquidar(ec.total_capital, ec.total_interes, ec.tasa_compensatoria.a_dominio(),
                       ec.tasa_moratoria.a_dominio(), ec.fecha_pago, hoy)
        deuda_al_dia += liq.total
    proximos = [ec.fecha_pago for ec in pend if ec.fecha_pago >= hoy]
    return dict(
        id=cliente.id, nombre=cliente.nombre_completo, tipo_documento=cliente.tipo_documento,
        numero_documento=cliente.numero_documento, telefono=cliente.telefono, moneda=cliente.moneda,
        estado=cliente.estado,
        linea=e.LineaCredito(limite=cliente.limite_credito, usado=usado, disponible=cliente.limite_credito - usado),
        deuda_pendiente=sum((ec.total_a_pagar for ec in pend), CERO), deuda_al_dia=deuda_al_dia,
        estados_vencidos=len(credito.vencidos(cliente, hoy)), proximo_vencimiento=min(proximos, default=None),
        score=score_de(s, cliente, hoy, usado), tiene_codigo=cliente.token_portal_hash is not None,
    )


def cliente_resumen(s: Session, cliente: m.Cliente, hoy: date) -> ClienteResumen:
    return ClienteResumen(**_resumen_campos(s, cliente, hoy))


def cliente_detalle(s: Session, cliente: m.Cliente, hoy: date) -> ClienteDetalle:
    return ClienteDetalle(
        **_resumen_campos(s, cliente, hoy),
        nombres=cliente.nombres, apellidos=cliente.apellidos, email=cliente.email, direccion=cliente.direccion,
        limite_credito=cliente.limite_credito, max_meses=cliente.max_meses, dia_corte=cliente.dia_corte,
        dia_pago=cliente.dia_pago, fecha_alta=cliente.fecha_alta,
        tasa_compensatoria=tasa_vista(cliente.tasa_compensatoria),
        tasa_moratoria=tasa_vista(cliente.tasa_moratoria),
        puede_cambiar_ciclo=not credito.tiene_deuda(s, cliente),
        ventas=[venta_vista(v, cliente) for v in reversed(cliente.ventas)],
        estados_cuenta=[estado_cuenta_vista(s, ec, hoy) for ec in reversed(cliente.estados_cuenta)],
        pagos=[pago_vista(p) for p in reversed(credito.pagos_del_cliente(s, cliente))],
    )
