"""Tablas de la base de datos (docs/modelo-datos.md)."""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import JSON, CheckConstraint, Date, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.bd import Base, Exacto
from app.finanzas.tasas import Periodo, Tasa as TasaDominio, TipoTasa

Dinero = Exacto(12, 2)
TasaFraccion = Exacto(12, 9)


class Tasa(Base):
    """Tasa pactada. Inmutable: un cambio de condiciones crea una fila nueva."""

    __tablename__ = "tasa"
    id: Mapped[int] = mapped_column(primary_key=True)
    tipo: Mapped[str] = mapped_column(String(10))
    periodo: Mapped[str] = mapped_column(String(15))
    valor: Mapped[Decimal] = mapped_column(Exacto(12, 7))
    capitalizacion: Mapped[str | None] = mapped_column(String(15))
    tea: Mapped[Decimal] = mapped_column(TasaFraccion)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    def a_dominio(self) -> TasaDominio:
        cap = Periodo(self.capitalizacion) if self.capitalizacion else None
        return TasaDominio(TipoTasa(self.tipo), Periodo(self.periodo), self.valor, cap)

    @classmethod
    def desde_dominio(cls, t: TasaDominio) -> "Tasa":
        return cls(tipo=t.tipo.value, periodo=t.periodo.value, valor=t.valor,
                   capitalizacion=t.capitalizacion.value if t.capitalizacion else None, tea=t.tea())


class Tienda(Base):
    __tablename__ = "tienda"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))
    giro: Mapped[str] = mapped_column(String(40))
    documento: Mapped[str | None] = mapped_column(String(11), unique=True)
    telefono: Mapped[str | None] = mapped_column(String(15))
    direccion: Mapped[str | None] = mapped_column(String(200))
    estado: Mapped[str] = mapped_column(String(10), default="ACTIVA")
    fecha_alta: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    fecha_baja: Mapped[datetime | None] = mapped_column(DateTime)
    configuracion: Mapped["ConfiguracionTienda"] = relationship(back_populates="tienda")


class ConfiguracionTienda(Base):
    __tablename__ = "configuracion_tienda"
    tienda_id: Mapped[int] = mapped_column(ForeignKey("tienda.id"), primary_key=True)
    moneda: Mapped[str] = mapped_column(String(3))
    limite_credito: Mapped[Decimal] = mapped_column(Dinero)
    max_meses: Mapped[int]
    dia_corte: Mapped[int]
    dia_pago: Mapped[int]
    tasa_compensatoria_id: Mapped[int] = mapped_column(ForeignKey("tasa.id"))
    tasa_moratoria_id: Mapped[int] = mapped_column(ForeignKey("tasa.id"))
    bloquear_con_vencido: Mapped[bool] = mapped_column(default=True)
    tienda: Mapped[Tienda] = relationship(back_populates="configuracion")
    tasa_compensatoria: Mapped[Tasa] = relationship(foreign_keys=[tasa_compensatoria_id])
    tasa_moratoria: Mapped[Tasa] = relationship(foreign_keys=[tasa_moratoria_id])
    __table_args__ = (
        CheckConstraint("dia_corte BETWEEN 1 AND 28"), CheckConstraint("dia_pago BETWEEN 1 AND 28"),
    )


class Usuario(Base):
    __tablename__ = "usuario"
    id: Mapped[int] = mapped_column(primary_key=True)
    usuario: Mapped[str] = mapped_column(String(60), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    rol: Mapped[str] = mapped_column(String(10))
    tienda_id: Mapped[int | None] = mapped_column(ForeignKey("tienda.id"))
    activo: Mapped[bool] = mapped_column(default=True)
    ultimo_acceso: Mapped[datetime | None] = mapped_column(DateTime)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    tienda: Mapped[Tienda | None] = relationship()


class Producto(Base):
    __tablename__ = "producto"
    id: Mapped[int] = mapped_column(primary_key=True)
    tienda_id: Mapped[int] = mapped_column(ForeignKey("tienda.id"))
    nombre: Mapped[str] = mapped_column(String(120))
    descripcion: Mapped[str | None] = mapped_column(String(500))
    marca: Mapped[str | None] = mapped_column(String(60))
    proveedor: Mapped[str | None] = mapped_column(String(120))
    unidad_medida: Mapped[str] = mapped_column(String(20))
    imagen_url: Mapped[str | None] = mapped_column(String(500))
    moneda: Mapped[str] = mapped_column(String(3))
    precio_contado: Mapped[Decimal] = mapped_column(Dinero)
    precio_lista: Mapped[Decimal] = mapped_column(Dinero)
    permite_pago_unico: Mapped[bool] = mapped_column(default=True)
    permite_cuotas: Mapped[bool] = mapped_column(default=False)
    activo: Mapped[bool] = mapped_column(default=True)


class Cliente(Base):
    __tablename__ = "cliente"
    id: Mapped[int] = mapped_column(primary_key=True)
    tienda_id: Mapped[int] = mapped_column(ForeignKey("tienda.id"))
    nombres: Mapped[str] = mapped_column(String(80))
    apellidos: Mapped[str] = mapped_column(String(80))
    tipo_documento: Mapped[str] = mapped_column(String(5))
    numero_documento: Mapped[str] = mapped_column(String(12))
    telefono: Mapped[str | None] = mapped_column(String(15))
    email: Mapped[str | None] = mapped_column(String(120))
    direccion: Mapped[str | None] = mapped_column(String(200))
    moneda: Mapped[str] = mapped_column(String(3))
    limite_credito: Mapped[Decimal] = mapped_column(Dinero)
    max_meses: Mapped[int]
    dia_corte: Mapped[int]
    dia_pago: Mapped[int]
    tasa_compensatoria_id: Mapped[int] = mapped_column(ForeignKey("tasa.id"))
    tasa_moratoria_id: Mapped[int] = mapped_column(ForeignKey("tasa.id"))
    token_portal_hash: Mapped[str | None] = mapped_column(String(255), index=True)
    estado: Mapped[str] = mapped_column(String(10), default="ACTIVO")
    fecha_alta: Mapped[date] = mapped_column(Date)
    tasa_compensatoria: Mapped[Tasa] = relationship(foreign_keys=[tasa_compensatoria_id])
    tasa_moratoria: Mapped[Tasa] = relationship(foreign_keys=[tasa_moratoria_id])
    ventas: Mapped[list["Venta"]] = relationship(back_populates="cliente", order_by="Venta.id")
    estados_cuenta: Mapped[list["EstadoCuenta"]] = relationship(
        back_populates="cliente", order_by="EstadoCuenta.fecha_corte")
    __table_args__ = (
        UniqueConstraint("tienda_id", "numero_documento"),
        CheckConstraint("dia_corte BETWEEN 1 AND 28"), CheckConstraint("dia_pago BETWEEN 1 AND 28"),
    )

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombres} {self.apellidos}"


class EstadoCuenta(Base):
    __tablename__ = "estado_cuenta"
    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("cliente.id"))
    periodo_desde: Mapped[date] = mapped_column(Date)
    fecha_corte: Mapped[date] = mapped_column(Date)
    fecha_pago: Mapped[date] = mapped_column(Date)
    moneda: Mapped[str] = mapped_column(String(3))
    tasa_compensatoria_id: Mapped[int] = mapped_column(ForeignKey("tasa.id"))
    tasa_moratoria_id: Mapped[int] = mapped_column(ForeignKey("tasa.id"))
    total_capital: Mapped[Decimal] = mapped_column(Dinero)
    total_interes: Mapped[Decimal] = mapped_column(Dinero)
    total_a_pagar: Mapped[Decimal] = mapped_column(Dinero)
    limite_credito: Mapped[Decimal] = mapped_column(Dinero)
    credito_usado: Mapped[Decimal] = mapped_column(Dinero)
    credito_disponible: Mapped[Decimal] = mapped_column(Dinero)
    estado: Mapped[str] = mapped_column(String(10), default="PENDIENTE")
    generado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    cliente: Mapped[Cliente] = relationship(back_populates="estados_cuenta")
    tasa_compensatoria: Mapped[Tasa] = relationship(foreign_keys=[tasa_compensatoria_id])
    tasa_moratoria: Mapped[Tasa] = relationship(foreign_keys=[tasa_moratoria_id])
    __table_args__ = (
        UniqueConstraint("cliente_id", "fecha_corte"),
        CheckConstraint("CAST(total_a_pagar AS REAL) > 0 OR estado = 'PAGADO'", name="ec_en_cero_pagado"),
    )

    @property
    def codigo(self) -> str:
        return f"EC-{self.fecha_corte:%Y-%m}"


class Venta(Base):
    __tablename__ = "venta"
    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("cliente.id"), index=True)
    fecha_hora: Mapped[datetime] = mapped_column(DateTime)
    modalidad: Mapped[str] = mapped_column(String(12))
    numero_cuotas: Mapped[int | None]
    moneda: Mapped[str] = mapped_column(String(3))
    tipo_cambio: Mapped[Decimal | None] = mapped_column(Exacto(8, 3))
    tasa_compensatoria_id: Mapped[int] = mapped_column(ForeignKey("tasa.id"))
    tasa_moratoria_id: Mapped[int] = mapped_column(ForeignKey("tasa.id"))
    fecha_corte: Mapped[date] = mapped_column(Date)
    fecha_pago: Mapped[date] = mapped_column(Date)
    capital: Mapped[Decimal] = mapped_column(Dinero)
    dias: Mapped[int]
    tasa_periodo: Mapped[Decimal] = mapped_column(TasaFraccion)
    interes: Mapped[Decimal] = mapped_column(Dinero)
    total: Mapped[Decimal] = mapped_column(Dinero)
    tem: Mapped[Decimal | None] = mapped_column(TasaFraccion)
    estado: Mapped[str] = mapped_column(String(10), default="VIGENTE")
    registrado_por: Mapped[int] = mapped_column(ForeignKey("usuario.id"))
    cliente: Mapped[Cliente] = relationship(back_populates="ventas")
    tasa_compensatoria: Mapped[Tasa] = relationship(foreign_keys=[tasa_compensatoria_id])
    tasa_moratoria: Mapped[Tasa] = relationship(foreign_keys=[tasa_moratoria_id])
    detalle: Mapped[list["VentaDetalle"]] = relationship(back_populates="venta", order_by="VentaDetalle.id")
    cuotas: Mapped[list["Cuota"]] = relationship(back_populates="venta", order_by="Cuota.numero")

    @property
    def fecha(self) -> date:
        return self.fecha_hora.date()

    @property
    def descripcion(self) -> str:
        return ", ".join(d.descripcion for d in self.detalle)


class VentaDetalle(Base):
    __tablename__ = "venta_detalle"
    id: Mapped[int] = mapped_column(primary_key=True)
    venta_id: Mapped[int] = mapped_column(ForeignKey("venta.id"))
    producto_id: Mapped[int] = mapped_column(ForeignKey("producto.id"))
    descripcion: Mapped[str] = mapped_column(String(120))
    cantidad: Mapped[Decimal] = mapped_column(Exacto(10, 3))
    precio_lista: Mapped[Decimal] = mapped_column(Dinero)
    moneda_producto: Mapped[str] = mapped_column(String(3))
    subtotal: Mapped[Decimal] = mapped_column(Dinero)
    venta: Mapped[Venta] = relationship(back_populates="detalle")


class Cuota(Base):
    __tablename__ = "cuota"
    id: Mapped[int] = mapped_column(primary_key=True)
    venta_id: Mapped[int] = mapped_column(ForeignKey("venta.id"))
    numero: Mapped[int]
    fecha_corte: Mapped[date] = mapped_column(Date)
    fecha_vencimiento: Mapped[date] = mapped_column(Date)
    saldo_inicial: Mapped[Decimal] = mapped_column(Dinero)
    interes: Mapped[Decimal] = mapped_column(Dinero)
    amortizacion: Mapped[Decimal] = mapped_column(Dinero)
    monto: Mapped[Decimal] = mapped_column(Dinero)
    saldo_final: Mapped[Decimal] = mapped_column(Dinero)
    libera_linea: Mapped[Decimal] = mapped_column(Dinero)
    estado: Mapped[str] = mapped_column(String(10), default="PENDIENTE")
    venta: Mapped[Venta] = relationship(back_populates="cuotas")
    __table_args__ = (UniqueConstraint("venta_id", "numero"),)


class Pago(Base):
    __tablename__ = "pago"
    id: Mapped[int] = mapped_column(primary_key=True)
    fecha_pago: Mapped[date] = mapped_column(Date)
    medio: Mapped[str] = mapped_column(String(15))
    total_mora: Mapped[Decimal] = mapped_column(Dinero)
    total_interes: Mapped[Decimal] = mapped_column(Dinero)
    total_capital: Mapped[Decimal] = mapped_column(Dinero)
    total: Mapped[Decimal] = mapped_column(Dinero)
    linea_liberada: Mapped[Decimal] = mapped_column(Dinero)
    estado: Mapped[str] = mapped_column(String(10), default="VALIDO")
    motivo_anulacion: Mapped[str | None] = mapped_column(String(200))
    anulado_en: Mapped[datetime | None] = mapped_column(DateTime)
    registrado_por: Mapped[int] = mapped_column(ForeignKey("usuario.id"))
    registrado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    detalle: Mapped[list["PagoDetalle"]] = relationship(back_populates="pago", order_by="PagoDetalle.id")


class PagoDetalle(Base):
    __tablename__ = "pago_detalle"
    id: Mapped[int] = mapped_column(primary_key=True)
    pago_id: Mapped[int] = mapped_column(ForeignKey("pago.id"))
    estado_cuenta_id: Mapped[int] = mapped_column(ForeignKey("estado_cuenta.id"), index=True)
    exigible: Mapped[Decimal] = mapped_column(Dinero)
    dias_mora: Mapped[int]
    tasa_compensatoria_mora: Mapped[Decimal] = mapped_column(TasaFraccion)
    interes_compensatorio_mora: Mapped[Decimal] = mapped_column(Dinero)
    tasa_moratoria: Mapped[Decimal] = mapped_column(TasaFraccion)
    interes_moratorio: Mapped[Decimal] = mapped_column(Dinero)
    interes: Mapped[Decimal] = mapped_column(Dinero)
    capital: Mapped[Decimal] = mapped_column(Dinero)
    total: Mapped[Decimal] = mapped_column(Dinero)
    pago: Mapped[Pago] = relationship(back_populates="detalle")
    estado_cuenta: Mapped[EstadoCuenta] = relationship()


class Auditoria(Base):
    __tablename__ = "auditoria"
    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    tienda_id: Mapped[int | None] = mapped_column(ForeignKey("tienda.id"))
    accion: Mapped[str] = mapped_column(String(40))
    entidad: Mapped[str] = mapped_column(String(30))
    entidad_id: Mapped[int | None]
    datos: Mapped[dict | None] = mapped_column(JSON)
    ip: Mapped[str | None] = mapped_column(String(45))
    fecha_hora: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class TipoCambio(Base):
    __tablename__ = "tipo_cambio"
    fecha: Mapped[date] = mapped_column(Date, primary_key=True)
    compra: Mapped[Decimal] = mapped_column(Exacto(8, 3))
    venta: Mapped[Decimal] = mapped_column(Exacto(8, 3))
    fuente: Mapped[str] = mapped_column(String(40))


class Sistema(Base):
    """Parámetros del sistema. Solo desarrollo: la fecha simulada para probar el paso del tiempo."""

    __tablename__ = "sistema"
    clave: Mapped[str] = mapped_column(String(40), primary_key=True)
    valor: Mapped[str] = mapped_column(String(200))
