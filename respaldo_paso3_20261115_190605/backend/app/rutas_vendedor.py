"""API del vendedor: requiere iniciar sesión.

Todas las rutas trabajan sobre la tienda del vendedor que inició sesión. Antes de
responder se generan los cortes pendientes hasta la fecha del sistema.
"""
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import modelos as m
from app.bd import sesion
from app.dominio import CERO, ReglaDeNegocio
from app.finanzas.redondeo import a_porcentaje
from app.json_exacto import exacto
from app.servicios import clientes as svc_clientes, credito, sistema, tipo_cambio, vistas
from app.servicios.seguridad import crear_token, leer_token, verificar_clave
from app.simulador.esquemas import Dinero, MedioPago, Moneda, TasaEntrada

router = APIRouter(prefix="/api")


# ---------------------------------------------------------------- Sesión

@dataclass
class Contexto:
    s: Session
    usuario: m.Usuario
    tienda: m.Tienda
    hoy: date


def contexto(authorization: str | None = Header(default=None), s: Session = Depends(sesion)) -> Contexto:
    token = (authorization or "").removeprefix("Bearer ").strip()
    usuario_id = leer_token(token) if token else None
    usuario = s.get(m.Usuario, usuario_id) if usuario_id else None
    if usuario is None or not usuario.activo or usuario.rol != "VENDEDOR":
        raise HTTPException(401, "Sesión no válida o vencida. Vuelva a iniciar sesión.")
    hoy = sistema.hoy(s)
    credito.ponerse_al_dia(s, hoy, tienda_id=usuario.tienda_id)
    return Contexto(s, usuario, usuario.tienda, hoy)


class Login(BaseModel):
    usuario: str
    clave: str


@router.post("/auth/login")
def iniciar_sesion(datos: Login, s: Session = Depends(sesion)):
    usuario = s.scalar(select(m.Usuario).where(m.Usuario.usuario == datos.usuario.strip()))
    if usuario is None or not usuario.activo or not verificar_clave(datos.clave, usuario.password_hash):
        raise HTTPException(401, "Usuario o contraseña incorrectos")
    usuario.ultimo_acceso = datetime.now()
    sistema.auditar(s, usuario, "LOGIN", "usuario", usuario.id)
    s.commit()
    return {"token": crear_token(usuario.id), "usuario": usuario.usuario, "tienda": usuario.tienda.nombre}


@router.get("/sesion")
def sesion_actual(c: Contexto = Depends(contexto)):
    real = sistema.fecha_real()
    return {"usuario": c.usuario.usuario, "tienda": c.tienda.nombre, "hoy": c.hoy,
            "fecha_real": real, "fecha_simulada": c.hoy != real}


class NuevaFecha(BaseModel):
    fecha: date


@router.post("/sistema/fecha")
def avanzar_fecha(datos: NuevaFecha, c: Contexto = Depends(contexto)):
    """Solo desarrollo: adelanta la fecha del sistema para probar cortes y mora."""
    sistema.avanzar(c.s, datos.fecha, c.usuario)
    c.s.commit()
    credito.ponerse_al_dia(c.s, datos.fecha, tienda_id=c.tienda.id)
    return {"hoy": datos.fecha}


# ---------------------------------------------------------------- Tienda y configuración

class ConfiguracionEntrada(BaseModel):
    moneda: Moneda
    limite_credito: Dinero = Field(gt=0)
    max_meses: int = Field(ge=1, le=36)
    dia_corte: int = Field(ge=1, le=28)
    dia_pago: int = Field(ge=1, le=28)
    tasa_compensatoria: TasaEntrada
    tasa_moratoria: TasaEntrada
    bloquear_con_vencido: bool


class TiendaEntrada(BaseModel):
    nombre: str = Field(min_length=2, max_length=120)
    giro: str = Field(min_length=2, max_length=40)
    documento: str | None = Field(default=None, pattern=r"^(\d{8}|\d{11})?$")
    telefono: str | None = Field(default=None, max_length=15)
    direccion: str | None = Field(default=None, max_length=200)
    configuracion: ConfiguracionEntrada


def _tienda(c: Contexto) -> dict:
    t, cfg = c.tienda, c.tienda.configuracion
    return exacto({
        "nombre": t.nombre, "giro": t.giro, "documento": t.documento, "telefono": t.telefono,
        "direccion": t.direccion,
        "configuracion": {
            "moneda": cfg.moneda, "limite_credito": cfg.limite_credito, "max_meses": cfg.max_meses,
            "dia_corte": cfg.dia_corte, "dia_pago": cfg.dia_pago,
            "tasa_compensatoria": vistas.tasa_vista(cfg.tasa_compensatoria),
            "tasa_moratoria": vistas.tasa_vista(cfg.tasa_moratoria),
            "bloquear_con_vencido": cfg.bloquear_con_vencido,
        },
    })


@router.get("/tienda")
def ver_tienda(c: Contexto = Depends(contexto)):
    return _tienda(c)


@router.put("/tienda")
def editar_tienda(datos: TiendaEntrada, c: Contexto = Depends(contexto)):
    t, cfg = c.tienda, c.tienda.configuracion
    t.nombre, t.giro = datos.nombre, datos.giro
    t.documento, t.telefono, t.direccion = datos.documento or None, datos.telefono or None, datos.direccion or None
    d = datos.configuracion
    cfg.moneda, cfg.limite_credito, cfg.max_meses = d.moneda, d.limite_credito, d.max_meses
    cfg.dia_corte, cfg.dia_pago, cfg.bloquear_con_vencido = d.dia_corte, d.dia_pago, d.bloquear_con_vencido
    cfg.tasa_compensatoria = svc_clientes.tasa_registrada(c.s, cfg.tasa_compensatoria, d.tasa_compensatoria.a_tasa())
    cfg.tasa_moratoria = svc_clientes.tasa_registrada(c.s, cfg.tasa_moratoria, d.tasa_moratoria.a_tasa())
    sistema.auditar(c.s, c.usuario, "EDITAR_TIENDA", "tienda", t.id)
    c.s.commit()
    return _tienda(c)


@router.get("/tipo-cambio")
def ver_tipo_cambio(c: Contexto = Depends(contexto)):
    tc = tipo_cambio.referencia(c.s, c.hoy)
    if tc is None:
        return None
    return exacto({"fecha": tc.fecha, "compra": tc.compra, "venta": tc.venta, "fuente": tc.fuente})


# ---------------------------------------------------------------- Catálogo

class ProductoEntrada(BaseModel):
    nombre: str = Field(min_length=2, max_length=120)
    descripcion: str | None = Field(default=None, max_length=500)
    marca: str | None = Field(default=None, max_length=60)
    proveedor: str | None = Field(default=None, max_length=120)
    unidad_medida: str = Field(min_length=1, max_length=20)
    imagen_url: str | None = Field(default=None, max_length=500)
    moneda: Moneda = "PEN"
    precio_contado: Dinero = Field(gt=0)
    precio_lista: Dinero = Field(gt=0)
    permite_pago_unico: bool = True
    permite_cuotas: bool = False
    activo: bool = True

    @model_validator(mode="after")
    def _reglas(self):
        if self.precio_lista < self.precio_contado:
            raise ValueError("El precio de lista (crédito) no puede ser menor que el precio al contado")
        if not (self.permite_pago_unico or self.permite_cuotas):
            raise ValueError("El producto debe permitir al menos una forma de pago")
        return self


def _producto(p: m.Producto) -> dict:
    return exacto({campo: getattr(p, campo) for campo in (
        "id", "nombre", "descripcion", "marca", "proveedor", "unidad_medida", "imagen_url", "moneda",
        "precio_contado", "precio_lista", "permite_pago_unico", "permite_cuotas", "activo")})


def _buscar_producto(c: Contexto, producto_id: int) -> m.Producto:
    p = c.s.get(m.Producto, producto_id)
    if p is None or p.tienda_id != c.tienda.id:
        raise HTTPException(404, "Producto no encontrado")
    return p


@router.get("/productos")
def listar_productos(c: Contexto = Depends(contexto)):
    productos = c.s.scalars(select(m.Producto).where(m.Producto.tienda_id == c.tienda.id).order_by(m.Producto.nombre))
    return [_producto(p) for p in productos]


@router.post("/productos")
def crear_producto(datos: ProductoEntrada, c: Contexto = Depends(contexto)):
    p = m.Producto(tienda_id=c.tienda.id, **datos.model_dump())
    c.s.add(p)
    c.s.flush()
    sistema.auditar(c.s, c.usuario, "CREAR_PRODUCTO", "producto", p.id, {"nombre": p.nombre})
    c.s.commit()
    return _producto(p)


@router.put("/productos/{producto_id}")
def editar_producto(producto_id: int, datos: ProductoEntrada, c: Contexto = Depends(contexto)):
    p = _buscar_producto(c, producto_id)
    for campo, valor in datos.model_dump().items():
        setattr(p, campo, valor)
    sistema.auditar(c.s, c.usuario, "EDITAR_PRODUCTO", "producto", p.id, {"activo": p.activo})
    c.s.commit()
    return _producto(p)


# ---------------------------------------------------------------- Clientes

class ClienteEntrada(BaseModel):
    nombres: str = Field(min_length=2, max_length=80)
    apellidos: str = Field(min_length=2, max_length=80)
    tipo_documento: Literal["DNI", "CE", "RUC"]
    numero_documento: str = Field(pattern=r"^\d{8,12}$")
    telefono: str | None = Field(default=None, pattern=r"^(\+?\d{6,14})?$")
    email: str | None = Field(default=None, max_length=120)
    direccion: str | None = Field(default=None, max_length=200)
    moneda: Moneda
    limite_credito: Dinero = Field(gt=0)
    max_meses: int = Field(ge=1, le=36)
    dia_corte: int = Field(ge=1, le=28)
    dia_pago: int = Field(ge=1, le=28)
    tasa_compensatoria: TasaEntrada
    tasa_moratoria: TasaEntrada

    @model_validator(mode="after")
    def _documento(self):
        largo = {"DNI": (8, 8), "RUC": (11, 11), "CE": (9, 12)}[self.tipo_documento]
        if not largo[0] <= len(self.numero_documento) <= largo[1]:
            raise ValueError(f"El {self.tipo_documento} debe tener {'-'.join(map(str, sorted(set(largo))))} dígitos")
        return self

    def datos(self) -> dict:
        d = self.model_dump(exclude={"tasa_compensatoria", "tasa_moratoria"})
        return {k: (v or None) if k in ("telefono", "email", "direccion") else v for k, v in d.items()}


def _buscar_cliente(c: Contexto, cliente_id: int) -> m.Cliente:
    cl = c.s.get(m.Cliente, cliente_id)
    if cl is None or cl.tienda_id != c.tienda.id:
        raise HTTPException(404, "Cliente no encontrado")
    return cl


@router.get("/clientes", response_model=list[vistas.ClienteResumen])
def listar_clientes(c: Contexto = Depends(contexto)):
    clientes = c.s.scalars(select(m.Cliente).where(m.Cliente.tienda_id == c.tienda.id)
                           .order_by(m.Cliente.apellidos, m.Cliente.nombres))
    return [vistas.cliente_resumen(c.s, cl, c.hoy) for cl in clientes]


@router.post("/clientes", response_model=vistas.ClienteDetalle)
def crear_cliente(datos: ClienteEntrada, c: Contexto = Depends(contexto)):
    cl = svc_clientes.crear_cliente(c.s, c.tienda.id, datos.datos(), datos.tasa_compensatoria.a_tasa(),
                                    datos.tasa_moratoria.a_tasa(), c.hoy, c.usuario)
    c.s.commit()
    return vistas.cliente_detalle(c.s, cl, c.hoy)


@router.get("/clientes/{cliente_id}", response_model=vistas.ClienteDetalle)
def ver_cliente(cliente_id: int, c: Contexto = Depends(contexto)):
    return vistas.cliente_detalle(c.s, _buscar_cliente(c, cliente_id), c.hoy)


@router.put("/clientes/{cliente_id}", response_model=vistas.ClienteDetalle)
def editar_cliente(cliente_id: int, datos: ClienteEntrada, c: Contexto = Depends(contexto)):
    cl = _buscar_cliente(c, cliente_id)
    svc_clientes.actualizar_cliente(c.s, cl, datos.datos(), datos.tasa_compensatoria.a_tasa(),
                                    datos.tasa_moratoria.a_tasa(), c.usuario)
    c.s.commit()
    return vistas.cliente_detalle(c.s, cl, c.hoy)


@router.post("/clientes/{cliente_id}/baja", response_model=vistas.ClienteDetalle)
def dar_de_baja(cliente_id: int, c: Contexto = Depends(contexto)):
    cl = _buscar_cliente(c, cliente_id)
    svc_clientes.dar_de_baja(c.s, cl, c.usuario)
    c.s.commit()
    return vistas.cliente_detalle(c.s, cl, c.hoy)


@router.post("/clientes/{cliente_id}/reactivar", response_model=vistas.ClienteDetalle)
def reactivar(cliente_id: int, c: Contexto = Depends(contexto)):
    cl = _buscar_cliente(c, cliente_id)
    svc_clientes.reactivar(c.s, cl, c.hoy, c.usuario)
    c.s.commit()
    return vistas.cliente_detalle(c.s, cl, c.hoy)


@router.post("/clientes/{cliente_id}/codigo")
def generar_codigo(cliente_id: int, c: Contexto = Depends(contexto)):
    """Genera un código nuevo para el portal; el anterior deja de funcionar."""
    codigo = svc_clientes.nuevo_codigo(c.s, _buscar_cliente(c, cliente_id), c.usuario)
    c.s.commit()
    return {"codigo": codigo}


# ---------------------------------------------------------------- Ventas

class ItemEntrada(BaseModel):
    producto_id: int
    cantidad: Decimal = Field(gt=0, max_digits=10, decimal_places=3)


class VentaEntrada(BaseModel):
    cliente_id: int
    items: list[ItemEntrada] = Field(min_length=1)
    modalidad: Literal["FIN_DE_MES", "CUOTAS"] = "FIN_DE_MES"
    numero_cuotas: int | None = Field(default=None, ge=1, le=36)
    tipo_cambio: Decimal | None = Field(default=None, gt=0, max_digits=8, decimal_places=3)


def _venta(c: Contexto, datos: VentaEntrada, confirmar: bool) -> tuple[m.Cliente, m.Venta]:
    cliente = _buscar_cliente(c, datos.cliente_id)
    items = [credito.ItemPedido(_buscar_producto(c, i.producto_id), i.cantidad) for i in datos.items]
    venta = credito.registrar_venta(c.s, cliente, items, datos.modalidad, datos.numero_cuotas,
                                    datos.tipo_cambio, c.hoy, c.usuario, confirmar=confirmar)
    return cliente, venta


@router.post("/ventas/previsualizar", response_model=vistas.VentaVista)
def previsualizar_venta(datos: VentaEntrada, c: Contexto = Depends(contexto)):
    cliente, venta = _venta(c, datos, confirmar=False)
    respuesta = vistas.venta_vista(venta, cliente)
    c.s.rollback()
    return respuesta


@router.post("/ventas", response_model=vistas.VentaVista)
def registrar_venta(datos: VentaEntrada, c: Contexto = Depends(contexto)):
    cliente, venta = _venta(c, datos, confirmar=True)
    c.s.commit()
    return vistas.venta_vista(venta, cliente)


@router.get("/ventas", response_model=list[vistas.VentaVista])
def listar_ventas(c: Contexto = Depends(contexto)):
    ventas = c.s.scalars(select(m.Venta).join(m.Cliente).where(m.Cliente.tienda_id == c.tienda.id)
                         .order_by(m.Venta.fecha_hora.desc()))
    return [vistas.venta_vista(v, v.cliente) for v in ventas]


@router.post("/ventas/{venta_id}/anular", response_model=vistas.VentaVista)
def anular_venta(venta_id: int, c: Contexto = Depends(contexto)):
    venta = c.s.get(m.Venta, venta_id)
    if venta is None or venta.cliente.tienda_id != c.tienda.id:
        raise HTTPException(404, "Venta no encontrada")
    credito.anular_venta(c.s, venta, c.hoy, c.usuario)
    c.s.commit()
    return vistas.venta_vista(venta, venta.cliente)


# ---------------------------------------------------------------- Estados de cuenta

@router.get("/estados-cuenta", response_model=list[vistas.EstadoCuentaVista])
def listar_estados(c: Contexto = Depends(contexto)):
    estados = c.s.scalars(select(m.EstadoCuenta).join(m.Cliente).where(m.Cliente.tienda_id == c.tienda.id)
                          .order_by(m.EstadoCuenta.fecha_corte.desc(), m.Cliente.apellidos))
    return [vistas.estado_cuenta_vista(c.s, ec, c.hoy) for ec in estados]


# ---------------------------------------------------------------- Pagos

class LiquidacionVista(BaseModel):
    cliente_id: int
    fecha: date
    pendientes: int
    detalle: list[dict]
    total_mora: Decimal
    total_recargo: Decimal
    total_interes: Decimal
    total_capital: Decimal
    total: Decimal
    linea_liberada: Decimal


@router.get("/clientes/{cliente_id}/liquidacion", response_model=LiquidacionVista)
def ver_liquidacion(cliente_id: int, cantidad: int = 1, c: Contexto = Depends(contexto)):
    """Cuánto pagaría hoy el cliente por sus `cantidad` estados de cuenta más antiguos."""
    cliente = _buscar_cliente(c, cliente_id)
    detalle = credito.liquidacion(c.s, cliente, cantidad, c.hoy)
    filas = [{
        "estado_cuenta": d.estado_cuenta.codigo, "fecha_pago_pactada": d.estado_cuenta.fecha_pago,
        "exigible": d.liquidacion.exigible, "dias_mora": d.liquidacion.dias_mora,
        "tasa_compensatoria_mora": a_porcentaje(d.liquidacion.tasa_compensatoria_mora),
        "interes_compensatorio_mora": d.liquidacion.interes_compensatorio_mora,
        "tasa_moratoria": a_porcentaje(d.liquidacion.tasa_moratoria),
        "interes_moratorio": d.liquidacion.interes_moratorio,
        "recargo_mora": d.liquidacion.total - d.liquidacion.exigible, "mora": d.liquidacion.mora,
        "interes": d.liquidacion.interes, "capital": d.liquidacion.capital, "total": d.liquidacion.total,
        "libera_linea": d.libera_linea,
    } for d in detalle]
    return LiquidacionVista(
        cliente_id=cliente.id, fecha=c.hoy, pendientes=len(credito.pendientes(cliente)), detalle=filas,
        total_mora=sum((d.liquidacion.mora for d in detalle), CERO),
        total_recargo=sum((d.liquidacion.total - d.liquidacion.exigible for d in detalle), CERO),
        total_interes=sum((d.liquidacion.interes for d in detalle), CERO),
        total_capital=sum((d.liquidacion.capital for d in detalle), CERO),
        total=sum((d.liquidacion.total for d in detalle), CERO),
        linea_liberada=sum((d.libera_linea for d in detalle), CERO),
    )


class PagoEntrada(BaseModel):
    cliente_id: int
    cantidad_estados: int = Field(default=1, ge=1)
    medio: MedioPago = "EFECTIVO"


@router.post("/pagos", response_model=vistas.PagoVista)
def registrar_pago(datos: PagoEntrada, c: Contexto = Depends(contexto)):
    cliente = _buscar_cliente(c, datos.cliente_id)
    pago = credito.registrar_pago(c.s, cliente, datos.cantidad_estados, datos.medio, c.hoy, c.usuario)
    c.s.commit()
    return vistas.pago_vista(pago)


@router.get("/pagos", response_model=list[vistas.PagoVista])
def listar_pagos(c: Contexto = Depends(contexto)):
    pagos = c.s.scalars(select(m.Pago).join(m.PagoDetalle).join(m.EstadoCuenta).join(m.Cliente)
                        .where(m.Cliente.tienda_id == c.tienda.id).distinct().order_by(m.Pago.id.desc()))
    return [vistas.pago_vista(p) for p in pagos]


class Anulacion(BaseModel):
    motivo: str = Field(min_length=3, max_length=200)


@router.post("/pagos/{pago_id}/anular", response_model=vistas.PagoVista)
def anular_pago(pago_id: int, datos: Anulacion, c: Contexto = Depends(contexto)):
    pago = c.s.get(m.Pago, pago_id)
    if pago is None or credito.cliente_del_pago(pago).tienda_id != c.tienda.id:
        raise HTTPException(404, "Pago no encontrado")
    credito.anular_pago(c.s, pago, datos.motivo, c.usuario)
    c.s.commit()
    return vistas.pago_vista(pago)


# ---------------------------------------------------------------- Panel y actividad

@router.get("/panel")
def panel(c: Contexto = Depends(contexto)):
    clientes = list(c.s.scalars(select(m.Cliente).where(m.Cliente.tienda_id == c.tienda.id,
                                                          m.Cliente.estado == "ACTIVO")))
    resumenes = [vistas.cliente_resumen(c.s, cl, c.hoy) for cl in clientes]
    proximos, vencidos = [], []
    for cl in clientes:
        for ec in credito.pendientes(cl):
            vista = vistas.estado_cuenta_vista(c.s, ec, c.hoy)
            fila = {"id": ec.id, "cliente_id": cl.id, "cliente": cl.nombre_completo, "codigo": ec.codigo,
                    "fecha_pago": ec.fecha_pago, "total": ec.total_a_pagar, "moneda": ec.moneda}
            if vista.deuda_al_dia:
                vencidos.append({**fila, "dias_mora": vista.deuda_al_dia.dias_mora,
                                 "total_hoy": vista.deuda_al_dia.total_a_pagar})
            else:
                proximos.append(fila)
    inicio_mes = c.hoy.replace(day=1)
    ventas_mes = list(c.s.scalars(select(m.Venta).join(m.Cliente).where(
        m.Cliente.tienda_id == c.tienda.id, m.Venta.estado != "ANULADA", m.Venta.fecha_hora >= inicio_mes)))
    actividad = c.s.scalars(select(m.Auditoria).where(m.Auditoria.tienda_id == c.tienda.id)
                            .order_by(m.Auditoria.id.desc()).limit(8))
    return exacto({
        "hoy": c.hoy,
        "clientes_activos": len(clientes),
        "credito_colocado": sum((r.linea.usado for r in resumenes), CERO),
        "por_cobrar": sum((Decimal(p["total"]) for p in proximos), CERO),
        "vencido_al_dia": sum((Decimal(v["total_hoy"]) for v in vencidos), CERO),
        "ventas_mes": {"cantidad": len(ventas_mes), "capital": sum((v.capital for v in ventas_mes), CERO)},
        "proximos": sorted(proximos, key=lambda p: p["fecha_pago"]),
        "vencidos": sorted(vencidos, key=lambda v: -v["dias_mora"]),
        "clientes": sorted([r.model_dump() for r in resumenes], key=lambda r: r["score"]["puntaje"]),
        "actividad": [_actividad(a) for a in actividad],
    })


def _actividad(a: m.Auditoria) -> dict:
    return {"id": a.id, "fecha_hora": a.fecha_hora, "accion": a.accion, "entidad": a.entidad,
            "entidad_id": a.entidad_id, "datos": a.datos, "automatico": a.usuario_id is None}


@router.get("/actividad")
def actividad(limite: int = 100, c: Contexto = Depends(contexto)):
    registros = c.s.scalars(select(m.Auditoria).where(m.Auditoria.tienda_id == c.tienda.id)
                            .order_by(m.Auditoria.id.desc()).limit(min(limite, 500)))
    return [_actividad(a) for a in registros]
