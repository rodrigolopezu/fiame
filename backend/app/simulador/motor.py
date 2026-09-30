"""Motor de simulación del crédito de un cliente.

Reproduce el funcionamiento del sistema (docs/funcionamiento.md) para un solo cliente:
avanza día por día desde el primer evento hasta `fecha_hasta`, procesa los eventos de
cada día y, al cierre del día de corte (23:59:59), genera el estado de cuenta.

Los algoritmos siguen docs/informe/07-algoritmo.md: RegistrarVenta, GenerarCronograma,
GenerarCorte y RegistrarPago.
"""
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal

from app.finanzas.cronograma import capitalizar, cronograma_frances, liberacion_de_linea
from app.finanzas.fechas import calcular_ciclo, dias_entre, fecha_pago_del_corte, sumar_meses
from app.finanzas.mora import intereses_por_mora
from app.finanzas.redondeo import a_porcentaje, r2
from app.finanzas.tasas import Tasa

from . import esquemas as e

CERO = Decimal("0.00")


class Rechazo(Exception):
    """Operación rechazada por una regla de negocio; el mensaje va a la bitácora."""


def soles(monto: Decimal, moneda: str) -> str:
    simbolo = "S/" if moneda == "PEN" else "US$"
    return f"{simbolo} {monto:,.2f}"


# ---------------------------------------------------------------- Estado interno

@dataclass
class Cuota:
    numero: int
    fecha_corte: date
    fecha_vencimiento: date
    saldo_inicial: Decimal
    interes: Decimal
    cuota: Decimal
    amortizacion: Decimal
    saldo_final: Decimal
    libera_linea: Decimal
    estado: str = "PENDIENTE"
    estado_cuenta: "EstadoCuenta | None" = None


@dataclass
class Venta:
    numero: int
    evento: int
    fecha: date
    modalidad: str
    numero_cuotas: int | None
    moneda: str
    tipo_cambio: Decimal | None
    items: list[e.ItemVentaSalida]
    capital: Decimal
    tasa_compensatoria: Tasa
    tasa_moratoria: Tasa
    fecha_corte: date
    fecha_pago: date
    dias: int
    tasa_periodo: Decimal
    interes: Decimal
    total: Decimal
    tem: Decimal | None = None
    cuotas: list[Cuota] = field(default_factory=list)
    estado: str = "VIGENTE"
    estado_cuenta: "EstadoCuenta | None" = None

    def descripcion(self) -> str:
        return ", ".join(i.descripcion for i in self.items)


@dataclass
class LineaEC:
    tipo: str
    venta: Venta
    cuota: Cuota | None

    @property
    def capital(self) -> Decimal:
        return self.cuota.amortizacion if self.cuota else self.venta.capital

    @property
    def interes(self) -> Decimal:
        return self.cuota.interes if self.cuota else self.venta.interes

    @property
    def total(self) -> Decimal:
        return self.cuota.cuota if self.cuota else self.venta.total

    @property
    def libera_linea(self) -> Decimal:
        return self.cuota.libera_linea if self.cuota else self.venta.capital


@dataclass
class EstadoCuenta:
    codigo: str
    periodo_desde: date
    fecha_corte: date
    fecha_pago: date
    tasa_compensatoria: Tasa
    tasa_moratoria: Tasa
    lineas: list[LineaEC]
    linea: e.LineaCredito
    vencidos_anteriores: list[e.VencidoInformativo]
    estado: str
    pagado_con: int | None = None

    @property
    def total_capital(self) -> Decimal:
        return sum((l.capital for l in self.lineas), CERO)

    @property
    def total_interes(self) -> Decimal:
        return sum((l.interes for l in self.lineas), CERO)

    @property
    def total_a_pagar(self) -> Decimal:
        return self.total_capital + self.total_interes


# ---------------------------------------------------------------- Simulador

class Simulador:
    def __init__(self, condiciones: e.Condiciones, fecha_hasta: date):
        self.c = condiciones
        self.fecha_hasta = fecha_hasta
        self.tasa_compensatoria = condiciones.tasa_compensatoria.a_tasa()
        self.tasa_moratoria = condiciones.tasa_moratoria.a_tasa()
        self.limite = condiciones.limite_credito
        self.usado = CERO
        self.ventas: list[Venta] = []
        self.estados: list[EstadoCuenta] = []
        self.pagos: list[e.PagoSalida] = []
        self.bitacora: list[e.RegistroBitacora] = []

    # -- utilidades

    def linea(self) -> e.LineaCredito:
        return e.LineaCredito(limite=self.limite, usado=self.usado, disponible=self.limite - self.usado)

    def anotar(self, evento: int | None, fecha: date, tipo: str, resultado: str, mensaje: str):
        self.bitacora.append(e.RegistroBitacora(
            evento=evento, fecha=fecha, tipo=tipo, resultado=resultado, mensaje=mensaje, linea=self.linea()))

    def pendientes(self) -> list[EstadoCuenta]:
        return [ec for ec in self.estados if ec.estado == "PENDIENTE"]

    def fmt(self, monto: Decimal) -> str:
        return soles(monto, self.c.moneda)

    # -- recorrido del tiempo

    def ejecutar(self, eventos: list[e.Evento]) -> e.ResultadoSimulacion:
        ordenados = sorted(enumerate(eventos), key=lambda par: par[1].fecha)
        dia = min((ev.fecha for ev in eventos), default=self.fecha_hasta)
        i = 0
        while dia <= self.fecha_hasta:
            while i < len(ordenados) and ordenados[i][1].fecha == dia:
                self.procesar(*ordenados[i])
                i += 1
            if dia.day == self.c.dia_corte:
                self.generar_corte(dia)
            dia += timedelta(days=1)
        for indice, evento in ordenados[i:]:
            self.anotar(indice, evento.fecha, evento.tipo, "RECHAZADO",
                        "La fecha del evento es posterior a la fecha de simulación")
        return self.resultado()

    def procesar(self, indice: int, evento: e.Evento):
        acciones = {
            "VENTA": self.registrar_venta,
            "PAGO": self.registrar_pago,
            "CAMBIO_CONDICIONES": self.cambiar_condiciones,
            "ANULAR_VENTA": self.anular_venta,
        }
        try:
            mensaje = acciones[evento.tipo](indice, evento)
            self.anotar(indice, evento.fecha, evento.tipo, "OK", mensaje)
        except Rechazo as rechazo:
            self.anotar(indice, evento.fecha, evento.tipo, "RECHAZADO", str(rechazo))

    # -- RegistrarVenta (7.4) y GenerarCronograma (7.5)

    def subtotal(self, item: e.ItemVenta, tipo_cambio: Decimal | None) -> Decimal:
        """Conversión de moneda: el tipo de cambio es soles por dólar."""
        importe = item.cantidad * item.precio_lista
        if item.moneda == self.c.moneda:
            return r2(importe)
        if tipo_cambio is None:
            raise Rechazo(f"'{item.descripcion}' está en {item.moneda}: se requiere el tipo de cambio")
        return r2(importe * tipo_cambio) if item.moneda == "USD" else r2(importe / tipo_cambio)

    def registrar_venta(self, indice: int, ev: e.EventoVenta) -> str:
        if self.c.bloquear_con_vencido:
            vencidos = [ec.codigo for ec in self.pendientes() if ec.fecha_pago < ev.fecha]
            if vencidos:
                raise Rechazo(f"El cliente tiene estados de cuenta vencidos: {', '.join(vencidos)}")
        items = [
            e.ItemVentaSalida(descripcion=it.descripcion, cantidad=it.cantidad, precio_lista=it.precio_lista,
                              moneda=it.moneda, subtotal=self.subtotal(it, ev.tipo_cambio))
            for it in ev.items
        ]
        capital = sum((it.subtotal for it in items), CERO)
        disponible = self.limite - self.usado
        if capital > disponible:
            raise Rechazo(f"El capital {self.fmt(capital)} excede el crédito disponible {self.fmt(disponible)}")

        corte, pago = calcular_ciclo(ev.fecha, self.c.dia_corte, self.c.dia_pago)
        tasa = self.tasa_compensatoria
        dias = dias_entre(ev.fecha, pago)
        tasa_periodo = tasa.efectiva(dias)
        venta = Venta(
            numero=len(self.ventas) + 1, evento=indice, fecha=ev.fecha, modalidad=ev.modalidad,
            numero_cuotas=ev.numero_cuotas if ev.modalidad == "CUOTAS" else None,
            moneda=self.c.moneda, tipo_cambio=ev.tipo_cambio, items=items, capital=capital,
            tasa_compensatoria=tasa, tasa_moratoria=self.tasa_moratoria,
            fecha_corte=corte, fecha_pago=pago, dias=dias, tasa_periodo=tasa_periodo,
            interes=CERO, total=CERO,
        )

        if ev.modalidad == "FIN_DE_MES":
            if not all(it.permite_pago_unico for it in ev.items):
                raise Rechazo("Algún producto no permite el pago único a fin de mes")
            venta.interes = r2(capital * tasa_periodo)
            venta.total = capital + venta.interes
            detalle = (f"fin de mes: {self.fmt(capital)} + interés {self.fmt(venta.interes)} "
                       f"({dias} días) = {self.fmt(venta.total)}, vence {pago:%d/%m/%Y}")
        else:
            if not all(it.permite_cuotas for it in ev.items):
                raise Rechazo("Algún producto no permite el pago en cuotas")
            n = ev.numero_cuotas
            if n is None or not 1 <= n <= self.c.max_meses:
                raise Rechazo(f"El número de cuotas debe estar entre 1 y {self.c.max_meses}")
            venta.total = capitalizar(capital, tasa_periodo)
            venta.interes = venta.total - capital
            venta.tem = tasa.tem()
            filas = cronograma_frances(venta.total, venta.tem, n)
            liberaciones = liberacion_de_linea(capital, [f.amortizacion for f in filas])
            for fila, libera in zip(filas, liberaciones):
                corte_k = sumar_meses(corte, fila.numero)
                venta.cuotas.append(Cuota(
                    numero=fila.numero, fecha_corte=corte_k,
                    fecha_vencimiento=fecha_pago_del_corte(corte_k, self.c.dia_pago),
                    saldo_inicial=fila.saldo_inicial, interes=fila.interes, cuota=fila.cuota,
                    amortizacion=fila.amortizacion, saldo_final=fila.saldo_final, libera_linea=libera,
                ))
            detalle = (f"{n} cuotas: {self.fmt(capital)} con {dias} días de gracia = "
                       f"{self.fmt(venta.total)}, primera cuota {self.fmt(venta.cuotas[0].cuota)} "
                       f"el {venta.cuotas[0].fecha_vencimiento:%d/%m/%Y}")

        self.ventas.append(venta)
        self.usado += capital
        return f"Venta {venta.numero}, {detalle}"

    # -- GenerarCorte (7.6)

    def generar_corte(self, dia: date):
        lineas = [LineaEC("COMPRA", v, None) for v in self.ventas
                  if v.modalidad == "FIN_DE_MES" and v.estado == "VIGENTE" and v.fecha_corte == dia]
        lineas += [LineaEC("CUOTA", v, c) for v in self.ventas if v.estado == "VIGENTE"
                   for c in v.cuotas if c.fecha_corte == dia and c.estado == "PENDIENTE"]
        lineas.sort(key=lambda l: (l.venta.fecha, l.venta.numero))

        ec = EstadoCuenta(
            codigo=f"EC-{dia:%Y-%m}", periodo_desde=sumar_meses(dia, -1) + timedelta(days=1),
            fecha_corte=dia, fecha_pago=fecha_pago_del_corte(dia, self.c.dia_pago),
            tasa_compensatoria=self.tasa_compensatoria, tasa_moratoria=self.tasa_moratoria,
            lineas=lineas, linea=self.linea(),
            vencidos_anteriores=[
                e.VencidoInformativo(codigo=v.codigo, fecha_pago=v.fecha_pago, exigible=v.total_a_pagar,
                                     dias_atraso=dias_entre(v.fecha_pago, dia))
                for v in self.pendientes() if v.fecha_pago < dia
            ],
            estado="PENDIENTE",
        )
        # Un EC sin deuda nace pagado: así nunca figura como vencido ni bloquea ventas.
        if ec.total_a_pagar == 0:
            ec.estado = "PAGADO"
        for l in lineas:
            if l.cuota:
                l.cuota.estado_cuenta = ec
            else:
                l.venta.estado_cuenta = ec
        self.estados.append(ec)
        if ec.total_a_pagar == 0:
            mensaje = f"{ec.codigo}: sin deuda en el periodo"
        else:
            mensaje = f"{ec.codigo}: total a pagar {self.fmt(ec.total_a_pagar)} hasta el {ec.fecha_pago:%d/%m/%Y}"
        self.anotar(None, dia, "CORTE", "OK", mensaje)

    # -- RegistrarPago (7.7)

    def registrar_pago(self, indice: int, ev: e.EventoPago) -> str:
        pendientes = self.pendientes()
        if not pendientes:
            raise Rechazo("No hay estados de cuenta pendientes de pago")
        if ev.cantidad_estados > len(pendientes):
            raise Rechazo(f"Solo hay {len(pendientes)} estado(s) de cuenta pendiente(s)")

        numero = len(self.pagos) + 1
        detalle = []
        for ec in pendientes[:ev.cantidad_estados]:
            exigible = ec.total_a_pagar
            dias_mora = max(0, dias_entre(ec.fecha_pago, ev.fecha))
            m = intereses_por_mora(exigible, ec.tasa_compensatoria, ec.tasa_moratoria, dias_mora)
            libera = sum((l.libera_linea for l in ec.lineas), CERO)
            detalle.append(e.DetallePagoSalida(
                estado_cuenta=ec.codigo, fecha_pago_pactada=ec.fecha_pago, exigible=exigible,
                dias_mora=dias_mora,
                tasa_compensatoria_mora=a_porcentaje(m.tasa_compensatoria),
                interes_compensatorio_mora=m.interes_compensatorio,
                tasa_moratoria=a_porcentaje(m.tasa_moratoria), interes_moratorio=m.interes_moratorio,
                mora=m.interes_moratorio, interes=ec.total_interes + m.interes_compensatorio,
                capital=ec.total_capital, total=exigible + m.total, libera_linea=libera,
            ))
            ec.estado, ec.pagado_con = "PAGADO", numero
            for l in ec.lineas:
                if l.cuota:
                    l.cuota.estado = "PAGADA"
                    if all(c.estado == "PAGADA" for c in l.venta.cuotas):
                        l.venta.estado = "PAGADA"
                else:
                    l.venta.estado = "PAGADA"

        pago = e.PagoSalida(
            numero=numero, evento=indice, fecha=ev.fecha, medio=ev.medio, detalle=detalle,
            total_mora=sum((d.mora for d in detalle), CERO),
            total_interes=sum((d.interes for d in detalle), CERO),
            total_capital=sum((d.capital for d in detalle), CERO),
            total=sum((d.total for d in detalle), CERO),
            linea_liberada=sum((d.libera_linea for d in detalle), CERO),
        )
        self.pagos.append(pago)
        self.usado -= pago.linea_liberada
        codigos = ", ".join(d.estado_cuenta for d in detalle)
        mora = f", con mora {self.fmt(pago.total_mora)}" if any(d.dias_mora for d in detalle) else ""
        return f"Pago {numero} de {codigos}: {self.fmt(pago.total)}{mora}"

    # -- Otros eventos

    def cambiar_condiciones(self, indice: int, ev: e.EventoCambioCondiciones) -> str:
        cambios = []
        if ev.tasa_compensatoria:
            self.tasa_compensatoria = ev.tasa_compensatoria.a_tasa()
            cambios.append(f"tasa compensatoria {self.tasa_compensatoria.descripcion()}")
        if ev.tasa_moratoria:
            self.tasa_moratoria = ev.tasa_moratoria.a_tasa()
            cambios.append(f"tasa moratoria {self.tasa_moratoria.descripcion()}")
        if ev.limite_credito:
            self.limite = ev.limite_credito
            cambios.append(f"límite {self.fmt(self.limite)}")
        if not cambios:
            raise Rechazo("No se indicó ningún cambio")
        return "Nuevas condiciones: " + ", ".join(cambios) + " (solo para ventas y cortes siguientes)"

    def anular_venta(self, indice: int, ev: e.EventoAnulacion) -> str:
        venta = next((v for v in self.ventas if v.numero == ev.venta), None)
        if venta is None:
            raise Rechazo(f"No existe la venta {ev.venta}")
        if venta.estado != "VIGENTE":
            raise Rechazo(f"La venta {venta.numero} ya está {venta.estado.lower()}")
        incluida = venta.estado_cuenta or next((c.estado_cuenta for c in venta.cuotas if c.estado_cuenta), None)
        if incluida:
            raise Rechazo(f"La venta {venta.numero} ya fue incluida en {incluida.codigo}")
        venta.estado = "ANULADA"
        self.usado -= venta.capital
        return f"Venta {venta.numero} anulada; se liberan {self.fmt(venta.capital)}"

    # -- Resultado

    def resumen_tasa(self, tasa: Tasa) -> e.ResumenTasa:
        return e.ResumenTasa(descripcion=tasa.descripcion(), tea=a_porcentaje(tasa.tea()),
                             tem=a_porcentaje(tasa.tem()))

    def salida_ec(self, ec: EstadoCuenta) -> e.EstadoCuentaSalida:
        estado, deuda = ec.estado, None
        if ec.estado == "PENDIENTE" and self.fecha_hasta > ec.fecha_pago:
            estado = "VENCIDO"
            dias_mora = dias_entre(ec.fecha_pago, self.fecha_hasta)
            m = intereses_por_mora(ec.total_a_pagar, ec.tasa_compensatoria, ec.tasa_moratoria, dias_mora)
            deuda = e.DeudaAlDia(
                fecha=self.fecha_hasta, dias_mora=dias_mora,
                tasa_compensatoria=a_porcentaje(m.tasa_compensatoria),
                interes_compensatorio=m.interes_compensatorio,
                tasa_moratoria=a_porcentaje(m.tasa_moratoria), interes_moratorio=m.interes_moratorio,
                total_a_pagar=ec.total_a_pagar + m.total,
            )
        return e.EstadoCuentaSalida(
            codigo=ec.codigo, periodo_desde=ec.periodo_desde, fecha_corte=ec.fecha_corte,
            fecha_pago=ec.fecha_pago, moneda=self.c.moneda,
            tasa_compensatoria=ec.tasa_compensatoria.descripcion(),
            tea_compensatoria=a_porcentaje(ec.tasa_compensatoria.tea()),
            tasa_moratoria=ec.tasa_moratoria.descripcion(),
            tea_moratoria=a_porcentaje(ec.tasa_moratoria.tea()),
            lineas=[
                e.LineaEstadoCuenta(
                    tipo=l.tipo, venta=l.venta.numero, fecha=l.venta.fecha, descripcion=l.venta.descripcion(),
                    cuota=f"{l.cuota.numero}/{l.venta.numero_cuotas}" if l.cuota else None,
                    capital=l.capital, dias=None if l.cuota else l.venta.dias,
                    tasa=a_porcentaje(l.venta.tem if l.cuota else l.venta.tasa_periodo),
                    interes=l.interes, total=l.total,
                )
                for l in ec.lineas
            ],
            total_capital=ec.total_capital, total_interes=ec.total_interes, total_a_pagar=ec.total_a_pagar,
            linea=ec.linea, vencidos_anteriores=ec.vencidos_anteriores, estado=estado,
            pagado_con=ec.pagado_con, deuda_al_dia=deuda,
        )

    def salida_venta(self, v: Venta) -> e.VentaSalida:
        return e.VentaSalida(
            numero=v.numero, evento=v.evento, fecha=v.fecha, modalidad=v.modalidad,
            numero_cuotas=v.numero_cuotas, moneda=v.moneda, tipo_cambio=v.tipo_cambio, items=v.items,
            capital=v.capital, tasa_compensatoria=v.tasa_compensatoria.descripcion(),
            tasa_moratoria=v.tasa_moratoria.descripcion(), fecha_corte=v.fecha_corte,
            fecha_pago=v.fecha_pago, dias=v.dias, tasa_periodo=a_porcentaje(v.tasa_periodo),
            interes=v.interes, total=v.total, tem=a_porcentaje(v.tem) if v.tem is not None else None,
            estado=v.estado, estado_cuenta=v.estado_cuenta.codigo if v.estado_cuenta else None,
            cuotas=[
                e.CuotaSalida(
                    numero=c.numero, fecha_corte=c.fecha_corte, fecha_vencimiento=c.fecha_vencimiento,
                    saldo_inicial=c.saldo_inicial, interes=c.interes, cuota=c.cuota,
                    amortizacion=c.amortizacion, saldo_final=c.saldo_final, libera_linea=c.libera_linea,
                    estado=c.estado, estado_cuenta=c.estado_cuenta.codigo if c.estado_cuenta else None,
                )
                for c in v.cuotas
            ],
        )

    def resultado(self) -> e.ResultadoSimulacion:
        return e.ResultadoSimulacion(
            fecha_hasta=self.fecha_hasta, moneda=self.c.moneda,
            tasa_compensatoria=self.resumen_tasa(self.tasa_compensatoria),
            tasa_moratoria=self.resumen_tasa(self.tasa_moratoria),
            linea=self.linea(), bitacora=self.bitacora,
            ventas=[self.salida_venta(v) for v in self.ventas],
            estados_cuenta=[self.salida_ec(ec) for ec in self.estados],
            pagos=self.pagos,
        )


def simular(solicitud: e.SolicitudSimulacion) -> e.ResultadoSimulacion:
    return Simulador(solicitud.condiciones, solicitud.fecha_hasta).ejecutar(solicitud.eventos)
