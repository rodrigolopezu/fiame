"""Operaciones de crédito sobre la base de datos: ventas, cortes y pagos.

Cada operación recibe la fecha en que ocurre y, antes de nada, genera los cortes que
falten hasta esa fecha. Así los estados de cuenta existen siempre que se necesitan, sin
depender de una tarea programada (GenerarCorte, 7.6).
"""
import threading
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import modelos as m
from app.dominio import CERO, Liquidacion, ReglaDeNegocio, calcular_venta, convertir, liquidar, validar_venta
from app.finanzas.fechas import fecha_pago_del_corte, sumar_meses
from app.servicios.sistema import auditar


# ---------------------------------------------------------------- Consultas básicas

def pagos_del_cliente(s: Session, cliente: m.Cliente, solo_validos: bool = False) -> list[m.Pago]:
    consulta = (select(m.Pago).join(m.PagoDetalle).join(m.EstadoCuenta)
                .where(m.EstadoCuenta.cliente_id == cliente.id).distinct().order_by(m.Pago.id))
    if solo_validos:
        consulta = consulta.where(m.Pago.estado == "VALIDO")
    return list(s.scalars(consulta))


def credito_usado(s: Session, cliente: m.Cliente) -> Decimal:
    """Capital de las ventas no anuladas menos lo liberado por pagos válidos."""
    capital = sum((v.capital for v in cliente.ventas if v.estado != "ANULADA"), CERO)
    liberado = sum((p.linea_liberada for p in pagos_del_cliente(s, cliente, solo_validos=True)), CERO)
    return capital - liberado


def pendientes(cliente: m.Cliente) -> list[m.EstadoCuenta]:
    return [ec for ec in cliente.estados_cuenta if ec.estado == "PENDIENTE"]


def vencidos(cliente: m.Cliente, fecha: date) -> list[m.EstadoCuenta]:
    return [ec for ec in pendientes(cliente) if ec.fecha_pago < fecha]


def tiene_deuda(s: Session, cliente: m.Cliente) -> bool:
    return credito_usado(s, cliente) > 0 or bool(pendientes(cliente))


def estado_cuenta_de(cliente: m.Cliente, fecha_corte: date) -> m.EstadoCuenta | None:
    return next((ec for ec in cliente.estados_cuenta if ec.fecha_corte == fecha_corte), None)


@dataclass
class LineaEC:
    tipo: str  # COMPRA | CUOTA
    venta: m.Venta
    cuota: m.Cuota | None

    @property
    def capital(self) -> Decimal:
        return self.cuota.amortizacion if self.cuota else self.venta.capital

    @property
    def interes(self) -> Decimal:
        return self.cuota.interes if self.cuota else self.venta.interes

    @property
    def total(self) -> Decimal:
        return self.cuota.monto if self.cuota else self.venta.total

    @property
    def libera_linea(self) -> Decimal:
        return self.cuota.libera_linea if self.cuota else self.venta.capital


def lineas_del_corte(cliente: m.Cliente, fecha_corte: date) -> list[LineaEC]:
    """Compras a fin de mes y cuotas que cobra el estado de cuenta de ese corte."""
    ventas = [v for v in cliente.ventas if v.estado != "ANULADA"]
    lineas = [LineaEC("COMPRA", v, None) for v in ventas
              if v.modalidad == "FIN_DE_MES" and v.fecha_corte == fecha_corte]
    lineas += [LineaEC("CUOTA", v, c) for v in ventas for c in v.cuotas if c.fecha_corte == fecha_corte]
    return sorted(lineas, key=lambda l: (l.venta.fecha_hora, l.venta.id))


# ---------------------------------------------------------------- Cortes (7.6)

def generar_cortes(s: Session, cliente: m.Cliente, hasta: date) -> list[m.EstadoCuenta]:
    """Genera los estados de cuenta de los cortes anteriores a `hasta` que falten.

    El corte cierra a las 23:59:59: el del mismo día `hasta` todavía no se genera.
    """
    if cliente.estado != "ACTIVO":
        return []
    ultimo = cliente.estados_cuenta[-1] if cliente.estados_cuenta else None
    inicio = ultimo.fecha_corte + timedelta(days=1) if ultimo else cliente.fecha_alta
    corte = date(inicio.year, inicio.month, cliente.dia_corte)
    if corte < inicio:
        corte = sumar_meses(corte, 1)
    nuevos = []
    while corte < hasta:
        nuevos.append(_generar_corte(s, cliente, corte))
        corte = sumar_meses(corte, 1)
    return nuevos


def _generar_corte(s: Session, cliente: m.Cliente, corte: date) -> m.EstadoCuenta:
    lineas = lineas_del_corte(cliente, corte)
    total_capital = sum((l.capital for l in lineas), CERO)
    total_interes = sum((l.interes for l in lineas), CERO)
    usado = credito_usado(s, cliente)
    ec = m.EstadoCuenta(
        cliente_id=cliente.id, periodo_desde=sumar_meses(corte, -1) + timedelta(days=1), fecha_corte=corte,
        fecha_pago=fecha_pago_del_corte(corte, cliente.dia_pago), moneda=cliente.moneda,
        tasa_compensatoria_id=cliente.tasa_compensatoria_id, tasa_moratoria_id=cliente.tasa_moratoria_id,
        total_capital=total_capital, total_interes=total_interes, total_a_pagar=total_capital + total_interes,
        limite_credito=cliente.limite_credito, credito_usado=usado, credito_disponible=cliente.limite_credito - usado,
        # Un EC sin deuda nace pagado: así nunca figura como vencido ni bloquea ventas.
        estado="PAGADO" if total_capital + total_interes == 0 else "PENDIENTE",
    )
    s.add(ec)
    s.flush()
    s.expire(cliente, ["estados_cuenta"])
    auditar(s, None, "GENERAR_CORTE", "estado_cuenta", ec.id,
            {"cliente": cliente.id, "corte": corte.isoformat(), "total": str(ec.total_a_pagar)},
            tienda_id=cliente.tienda_id)
    return ec


# Varias peticiones pueden llegar a la vez y querer generar el mismo corte: se generan de a una.
_candado_cortes = threading.Lock()


def ponerse_al_dia(s: Session, hasta: date, tienda_id: int | None = None, cliente: m.Cliente | None = None):
    """Genera y guarda los cortes pendientes de una tienda o de un cliente hasta `hasta`."""
    with _candado_cortes:
        try:
            if cliente is not None:
                generar_cortes(s, cliente, hasta)
            else:
                for c in s.scalars(select(m.Cliente).where(m.Cliente.tienda_id == tienda_id,
                                                           m.Cliente.estado == "ACTIVO")):
                    generar_cortes(s, c, hasta)
            s.commit()
        except IntegrityError:
            # Otro proceso ya generó el mismo corte (la base de datos garantiza uno por cliente y fecha).
            s.rollback()


# ---------------------------------------------------------------- Ventas (7.4 y 7.5)

@dataclass
class ItemPedido:
    producto: m.Producto
    cantidad: Decimal


def registrar_venta(s: Session, cliente: m.Cliente, items: list[ItemPedido], modalidad: str,
                    numero_cuotas: int | None, tipo_cambio: Decimal | None, fecha: date,
                    usuario: m.Usuario, confirmar: bool = True) -> m.Venta:
    """Valida y calcula una venta. Con `confirmar=False` solo la calcula (vista previa)."""
    generar_cortes(s, cliente, fecha)
    if cliente.estado != "ACTIVO":
        raise ReglaDeNegocio("El cliente está dado de baja")
    if not items:
        raise ReglaDeNegocio("La venta debe tener al menos un producto")
    for it in items:
        if not it.producto.activo:
            raise ReglaDeNegocio(f"'{it.producto.nombre}' no está disponible en el catálogo")
        if it.cantidad <= 0:
            raise ReglaDeNegocio("La cantidad debe ser mayor que cero")

    detalle = [
        m.VentaDetalle(producto_id=it.producto.id, descripcion=it.producto.nombre, cantidad=it.cantidad,
                       precio_lista=it.producto.precio_lista, moneda_producto=it.producto.moneda,
                       subtotal=convertir(it.cantidad * it.producto.precio_lista, it.producto.moneda,
                                          cliente.moneda, tipo_cambio, it.producto.nombre))
        for it in items
    ]
    capital = sum((d.subtotal for d in detalle), CERO)
    configuracion = s.get(m.ConfiguracionTienda, cliente.tienda_id)
    validar_venta(
        modalidad=modalidad, numero_cuotas=numero_cuotas, max_meses=cliente.max_meses,
        todos_pago_unico=all(it.producto.permite_pago_unico for it in items),
        todos_cuotas=all(it.producto.permite_cuotas for it in items),
        capital=capital, disponible=cliente.limite_credito - credito_usado(s, cliente), moneda=cliente.moneda,
        vencidos=[ec.codigo for ec in vencidos(cliente, fecha)],
        bloquear_con_vencido=configuracion.bloquear_con_vencido,
    )
    calculo = calcular_venta(capital, cliente.tasa_compensatoria.a_dominio(), fecha, cliente.dia_corte,
                             cliente.dia_pago, modalidad, numero_cuotas)
    otra_moneda = any(it.producto.moneda != cliente.moneda for it in items)
    venta = m.Venta(
        cliente_id=cliente.id, fecha_hora=datetime.combine(fecha, datetime.now().time()),
        modalidad=modalidad, numero_cuotas=numero_cuotas if modalidad == "CUOTAS" else None,
        moneda=cliente.moneda, tipo_cambio=tipo_cambio if otra_moneda else None,
        tasa_compensatoria=cliente.tasa_compensatoria, tasa_moratoria=cliente.tasa_moratoria,
        fecha_corte=calculo.fecha_corte, fecha_pago=calculo.fecha_pago, capital=capital, dias=calculo.dias,
        tasa_periodo=calculo.tasa_periodo, interes=calculo.interes, total=calculo.total, tem=calculo.tem,
        estado="VIGENTE", registrado_por=usuario.id, detalle=detalle,
        cuotas=[
            m.Cuota(numero=c.numero, fecha_corte=c.fecha_corte, fecha_vencimiento=c.fecha_vencimiento,
                    saldo_inicial=c.saldo_inicial, interes=c.interes, amortizacion=c.amortizacion,
                    monto=c.cuota, saldo_final=c.saldo_final, libera_linea=c.libera_linea, estado="PENDIENTE")
            for c in calculo.cuotas
        ],
    )
    if confirmar:
        s.add(venta)
        s.flush()
        s.expire(cliente, ["ventas"])
        auditar(s, usuario, "REGISTRAR_VENTA", "venta", venta.id, {
            "cliente": cliente.id, "modalidad": modalidad, "capital": str(capital), "total": str(venta.total)})
    return venta


def anular_venta(s: Session, venta: m.Venta, fecha: date, usuario: m.Usuario):
    cliente = venta.cliente
    generar_cortes(s, cliente, fecha)
    if venta.estado != "VIGENTE":
        raise ReglaDeNegocio(f"La venta {venta.id} ya está {venta.estado.lower()}")
    cortes = [venta.fecha_corte] if venta.modalidad == "FIN_DE_MES" else [c.fecha_corte for c in venta.cuotas]
    incluida = next((ec for corte in cortes if (ec := estado_cuenta_de(cliente, corte))), None)
    if incluida:
        raise ReglaDeNegocio(f"La venta {venta.id} ya fue incluida en {incluida.codigo}; no se puede anular")
    venta.estado = "ANULADA"
    auditar(s, usuario, "ANULAR_VENTA", "venta", venta.id, {"cliente": cliente.id, "capital": str(venta.capital)})


# ---------------------------------------------------------------- Pagos (7.7)

@dataclass
class DetalleLiquidacion:
    estado_cuenta: m.EstadoCuenta
    liquidacion: Liquidacion
    libera_linea: Decimal


def liquidacion(s: Session, cliente: m.Cliente, cantidad: int, fecha: date) -> list[DetalleLiquidacion]:
    """Cuánto debe pagar hoy por sus `cantidad` estados de cuenta pendientes más antiguos."""
    generar_cortes(s, cliente, fecha)
    pend = pendientes(cliente)
    if not pend:
        raise ReglaDeNegocio("El cliente no tiene estados de cuenta pendientes de pago")
    if not 1 <= cantidad <= len(pend):
        raise ReglaDeNegocio(f"Se pueden pagar entre 1 y {len(pend)} estado(s) de cuenta")
    detalle = []
    for ec in pend[:cantidad]:
        liq = liquidar(ec.total_capital, ec.total_interes, ec.tasa_compensatoria.a_dominio(),
                       ec.tasa_moratoria.a_dominio(), ec.fecha_pago, fecha)
        libera = sum((l.libera_linea for l in lineas_del_corte(cliente, ec.fecha_corte)), CERO)
        detalle.append(DetalleLiquidacion(ec, liq, libera))
    return detalle


def _marcar_lineas(cliente: m.Cliente, ec: m.EstadoCuenta, pagado: bool):
    for linea in lineas_del_corte(cliente, ec.fecha_corte):
        if linea.cuota:
            linea.cuota.estado = "PAGADA" if pagado else "PENDIENTE"
            linea.venta.estado = "PAGADA" if all(c.estado == "PAGADA" for c in linea.venta.cuotas) else "VIGENTE"
        else:
            linea.venta.estado = "PAGADA" if pagado else "VIGENTE"


def registrar_pago(s: Session, cliente: m.Cliente, cantidad: int, medio: str, fecha: date,
                   usuario: m.Usuario) -> m.Pago:
    detalle = liquidacion(s, cliente, cantidad, fecha)
    pago = m.Pago(
        fecha_pago=fecha, medio=medio, registrado_por=usuario.id,
        total_mora=sum((d.liquidacion.mora for d in detalle), CERO),
        total_interes=sum((d.liquidacion.interes for d in detalle), CERO),
        total_capital=sum((d.liquidacion.capital for d in detalle), CERO),
        total=sum((d.liquidacion.total for d in detalle), CERO),
        linea_liberada=sum((d.libera_linea for d in detalle), CERO),
        detalle=[
            m.PagoDetalle(
                estado_cuenta_id=d.estado_cuenta.id, exigible=d.liquidacion.exigible,
                dias_mora=d.liquidacion.dias_mora, tasa_compensatoria_mora=d.liquidacion.tasa_compensatoria_mora,
                interes_compensatorio_mora=d.liquidacion.interes_compensatorio_mora,
                tasa_moratoria=d.liquidacion.tasa_moratoria, interes_moratorio=d.liquidacion.interes_moratorio,
                interes=d.liquidacion.interes, capital=d.liquidacion.capital, total=d.liquidacion.total,
            )
            for d in detalle
        ],
    )
    for d in detalle:
        d.estado_cuenta.estado = "PAGADO"
        _marcar_lineas(cliente, d.estado_cuenta, pagado=True)
    s.add(pago)
    s.flush()
    auditar(s, usuario, "REGISTRAR_PAGO", "pago", pago.id, {
        "cliente": cliente.id, "estados_cuenta": [d.estado_cuenta.codigo for d in detalle],
        "total": str(pago.total), "mora": str(pago.total_mora)})
    return pago


def cliente_del_pago(pago: m.Pago) -> m.Cliente:
    return pago.detalle[0].estado_cuenta.cliente


def anular_pago(s: Session, pago: m.Pago, motivo: str, usuario: m.Usuario):
    """Un pago no se borra: se anula con motivo. Solo el último pago válido del cliente,
    para respetar el orden de pago del más antiguo al más reciente."""
    if pago.estado != "VALIDO":
        raise ReglaDeNegocio("El pago ya está anulado")
    if not motivo.strip():
        raise ReglaDeNegocio("Indique el motivo de la anulación")
    cliente = cliente_del_pago(pago)
    if pagos_del_cliente(s, cliente, solo_validos=True)[-1].id != pago.id:
        raise ReglaDeNegocio("Solo se puede anular el último pago válido del cliente")
    pago.estado, pago.motivo_anulacion, pago.anulado_en = "ANULADO", motivo.strip(), datetime.now()
    for d in pago.detalle:
        d.estado_cuenta.estado = "PENDIENTE"
        _marcar_lineas(cliente, d.estado_cuenta, pagado=False)
    auditar(s, usuario, "ANULAR_PAGO", "pago", pago.id, {"cliente": cliente.id, "motivo": pago.motivo_anulacion})
