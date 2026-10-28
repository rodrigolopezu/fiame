"""Alta, edición y baja de clientes, y su código de acceso al portal."""
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import modelos as m
from app.dominio import ReglaDeNegocio
from app.finanzas.tasas import Tasa as TasaDominio
from app.servicios.credito import tiene_deuda
from app.servicios.seguridad import generar_codigo, hash_codigo
from app.servicios.sistema import auditar


def tasa_registrada(s: Session, actual: m.Tasa | None, nueva: TasaDominio) -> m.Tasa:
    """Las tasas son inmutables: si cambió algún dato se crea una fila nueva."""
    if actual is not None and actual.a_dominio() == nueva:
        return actual
    fila = m.Tasa.desde_dominio(nueva)
    s.add(fila)
    s.flush()
    return fila


def validar_documento_unico(s: Session, tienda_id: int, numero: str, excepto: int | None = None):
    existente = s.scalar(select(m.Cliente).where(
        m.Cliente.tienda_id == tienda_id, m.Cliente.numero_documento == numero))
    if existente and existente.id != excepto:
        raise ReglaDeNegocio(f"Ya existe un cliente con el documento {numero}")


def crear_cliente(s: Session, tienda_id: int, datos: dict, compensatoria: TasaDominio,
                  moratoria: TasaDominio, fecha: date, usuario: m.Usuario) -> m.Cliente:
    validar_documento_unico(s, tienda_id, datos["numero_documento"])
    cliente = m.Cliente(
        tienda_id=tienda_id, fecha_alta=fecha, estado="ACTIVO",
        tasa_compensatoria=tasa_registrada(s, None, compensatoria),
        tasa_moratoria=tasa_registrada(s, None, moratoria), **datos,
    )
    s.add(cliente)
    s.flush()
    auditar(s, usuario, "CREAR_CLIENTE", "cliente", cliente.id,
            {"nombre": cliente.nombre_completo, "limite": str(cliente.limite_credito)})
    return cliente


CAMPOS_DEL_CICLO = ("moneda", "dia_corte", "dia_pago")


def actualizar_cliente(s: Session, cliente: m.Cliente, datos: dict, compensatoria: TasaDominio,
                       moratoria: TasaDominio, usuario: m.Usuario) -> m.Cliente:
    """Los días de corte y pago y la moneda no cambian si el cliente tiene deuda pendiente,
    porque las fechas y montos ya calculados dependen de ellos."""
    cambios_ciclo = [c for c in CAMPOS_DEL_CICLO if datos[c] != getattr(cliente, c)]
    if cambios_ciclo and tiene_deuda(s, cliente):
        raise ReglaDeNegocio("No se puede cambiar la moneda ni los días de corte o pago mientras el cliente tenga deuda")
    validar_documento_unico(s, cliente.tienda_id, datos["numero_documento"], excepto=cliente.id)
    antes = {"limite": str(cliente.limite_credito), "tasa": cliente.tasa_compensatoria.a_dominio().descripcion()}
    for campo, valor in datos.items():
        setattr(cliente, campo, valor)
    cliente.tasa_compensatoria = tasa_registrada(s, cliente.tasa_compensatoria, compensatoria)
    cliente.tasa_moratoria = tasa_registrada(s, cliente.tasa_moratoria, moratoria)
    auditar(s, usuario, "EDITAR_CLIENTE", "cliente", cliente.id, {"antes": antes, "despues": {
        "limite": str(cliente.limite_credito), "tasa": compensatoria.descripcion()}})
    return cliente


def dar_de_baja(s: Session, cliente: m.Cliente, usuario: m.Usuario):
    if tiene_deuda(s, cliente):
        raise ReglaDeNegocio("No se puede dar de baja a un cliente con deuda pendiente")
    cliente.estado = "BAJA"
    cliente.token_portal_hash = None
    auditar(s, usuario, "BAJA_CLIENTE", "cliente", cliente.id)


def reactivar(s: Session, cliente: m.Cliente, fecha: date, usuario: m.Usuario):
    cliente.estado = "ACTIVO"
    # Los cortes vuelven a generarse desde la reactivación.
    cliente.fecha_alta = max(cliente.fecha_alta, fecha)
    auditar(s, usuario, "REACTIVAR_CLIENTE", "cliente", cliente.id)


def nuevo_codigo(s: Session, cliente: m.Cliente, usuario: m.Usuario | None, codigo: str | None = None) -> str:
    """Genera (o regenera) el código del portal. El anterior deja de funcionar."""
    if cliente.estado != "ACTIVO":
        raise ReglaDeNegocio("El cliente está dado de baja")
    codigo = codigo or generar_codigo()
    cliente.token_portal_hash = hash_codigo(codigo)
    auditar(s, usuario, "GENERAR_CODIGO_PORTAL", "cliente", cliente.id, tienda_id=cliente.tienda_id)
    return codigo


def buscar_por_codigo(s: Session, codigo: str) -> m.Cliente | None:
    return s.scalar(select(m.Cliente).where(
        m.Cliente.token_portal_hash == hash_codigo(codigo), m.Cliente.estado == "ACTIVO"))


def uso_de_linea(usado: Decimal, limite: Decimal) -> Decimal:
    return usado / limite if limite > 0 else Decimal("1")
