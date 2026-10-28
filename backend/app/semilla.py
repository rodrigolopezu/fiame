"""Datos de prueba: una tienda, su vendedor, 12 productos y 2 clientes con historial.

El historial se registra con los mismos servicios que usa la aplicación, en orden
cronológico, así que los montos son los que calcularía el sistema.

Reiniciar la base de datos:  python -m app.semilla --reiniciar
"""
import sys
from datetime import date
from decimal import Decimal as D

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import modelos as m
from app.bd import RUTA_BD, Base, Sesion, motor
from app.finanzas.tasas import Periodo, Tasa, TipoTasa
from app.servicios import clientes, credito
from app.servicios.seguridad import hash_clave

USUARIO, CLAVE = "vendedor", "fiame2026"
CODIGOS = {"45781236": "J7KQ-M4HP", "70412589": "A7NT-X4PL"}

PRODUCTOS = [
    # nombre, marca, unidad, moneda, contado, lista, pago único, cuotas, imagen
    ("Arroz extra 5 kg", "Costeño", "bolsa", "PEN", "20.50", "22.00", True, False, "arroz"),
    ("Aceite vegetal 1 L", "Primor", "botella", "PEN", "9.00", "9.50", True, False, "aceite"),
    ("Azúcar rubia 1 kg", "Dulfina", "bolsa", "PEN", "4.20", "4.50", True, False, "azucar"),
    ("Leche evaporada x6", "Gloria", "paquete", "PEN", "22.50", "24.00", True, False, "leche"),
    ("Atún en trozos x3", "Florida", "paquete", "PEN", "16.50", "17.70", True, False, "atun"),
    ("Fideos spaghetti 950 g", "Don Vittorio", "bolsa", "PEN", "5.40", "5.80", True, False, "fideos"),
    ("Detergente 2.6 kg", "Bolívar", "bolsa", "PEN", "27.90", "29.90", True, False, "detergente"),
    ("Papel higiénico x12", "Elite", "paquete", "PEN", "18.90", "19.90", True, False, "papel"),
    ("Gaseosa 3 L", "Inca Kola", "botella", "PEN", "11.50", "12.00", True, False, "gaseosa"),
    ("Huevos rosados x30", "La Calera", "bandeja", "PEN", "17.00", "18.00", True, False, "huevos"),
    ("Licuadora 3 velocidades", "Oster", "unidad", "PEN", "149.00", "165.00", True, True, "licuadora"),
    ("Parlante Bluetooth (importado)", "JBL", "unidad", "USD", "45.00", "49.90", True, True, "parlante"),
]


def _tasa(s: Session, tipo, valor, capitalizacion=None) -> m.Tasa:
    return clientes.tasa_registrada(s, None, Tasa(tipo, Periodo.ANUAL, D(valor), capitalizacion))


def sembrar(s: Session) -> bool:
    """Carga los datos de prueba si la base está vacía. Devuelve True si sembró."""
    if s.scalar(select(m.Tienda)):
        return False

    tienda = m.Tienda(nombre="Bodega Doña Rosa", giro="Bodega", documento="10456789012",
                      telefono="987111222", direccion="Av. Los Próceres 1234, San Juan de Lurigancho")
    s.add(tienda)
    s.flush()
    s.add(m.ConfiguracionTienda(
        tienda_id=tienda.id, moneda="PEN", limite_credito=D("500.00"), max_meses=6, dia_corte=20, dia_pago=26,
        tasa_compensatoria=_tasa(s, TipoTasa.EFECTIVA, "24"), tasa_moratoria=_tasa(s, TipoTasa.EFECTIVA, "36"),
        bloquear_con_vencido=True))
    vendedor = m.Usuario(usuario=USUARIO, password_hash=hash_clave(CLAVE), rol="VENDEDOR", tienda_id=tienda.id)
    s.add(vendedor)
    s.add(m.TipoCambio(fecha=date(2026, 7, 27), compra=D("3.512"), venta=D("3.520"),
                       fuente="Referencial (datos de prueba)"))

    productos = {}
    for nombre, marca, unidad, moneda, contado, lista, unico, cuotas, imagen in PRODUCTOS:
        p = m.Producto(tienda_id=tienda.id, nombre=nombre, marca=marca, unidad_medida=unidad, moneda=moneda,
                       precio_contado=D(contado), precio_lista=D(lista), permite_pago_unico=unico,
                       permite_cuotas=cuotas, imagen_url=f"/productos/{imagen}.svg",
                       proveedor="Distribuidora Lima Norte" if moneda == "PEN" else "Importaciones Andinas")
        s.add(p)
        productos[imagen] = p
    s.flush()

    def pedido(*pares):
        return [credito.ItemPedido(productos[clave], D(cantidad)) for clave, cantidad in pares]

    # Cliente 1: tasa efectiva, paga a tiempo salvo una vez (score verde).
    juan = clientes.crear_cliente(s, tienda.id, dict(
        nombres="Juan", apellidos="Pérez Quispe", tipo_documento="DNI", numero_documento="45781236",
        telefono="987654321", email=None, direccion="Jr. Los Olivos 245", moneda="PEN",
        limite_credito=D("500.00"), max_meses=3, dia_corte=20, dia_pago=26,
    ), Tasa(TipoTasa.EFECTIVA, Periodo.ANUAL, D("24")), Tasa(TipoTasa.EFECTIVA, Periodo.ANUAL, D("36")),
        date(2026, 7, 1), vendedor)
    credito.registrar_venta(s, juan, pedido(("arroz", "1")), "FIN_DE_MES", None, None, date(2026, 7, 10), vendedor)
    credito.registrar_venta(s, juan, pedido(("licuadora", "1")), "CUOTAS", 3, None, date(2026, 7, 15), vendedor)
    credito.registrar_pago(s, juan, 1, "EFECTIVO", date(2026, 7, 25), vendedor)
    credito.registrar_venta(s, juan, pedido(("aceite", "2"), ("azucar", "2")), "FIN_DE_MES", None, None,
                            date(2026, 8, 5), vendedor)
    credito.registrar_pago(s, juan, 1, "YAPE", date(2026, 8, 29), vendedor)
    credito.registrar_venta(s, juan, pedido(("fideos", "3"), ("atun", "1")), "FIN_DE_MES", None, None,
                            date(2026, 9, 12), vendedor)
    credito.registrar_venta(s, juan, pedido(("gaseosa", "2")), "FIN_DE_MES", None, None, date(2026, 9, 24), vendedor)
    credito.registrar_pago(s, juan, 1, "EFECTIVO", date(2026, 9, 26), vendedor)

    # Cliente 2: tasa nominal, compra en dólares y un estado de cuenta vencido (score rojo).
    ana = clientes.crear_cliente(s, tienda.id, dict(
        nombres="Ana", apellidos="Torres Ríos", tipo_documento="DNI", numero_documento="70412589",
        telefono="912345678", email="ana.torres@correo.pe", direccion="Calle Las Begonias 118", moneda="PEN",
        limite_credito=D("800.00"), max_meses=6, dia_corte=25, dia_pago=5,
    ), Tasa(TipoTasa.NOMINAL, Periodo.ANUAL, D("30"), Periodo.MENSUAL),
        Tasa(TipoTasa.NOMINAL, Periodo.ANUAL, D("36"), Periodo.DIARIA), date(2026, 7, 1), vendedor)
    credito.registrar_venta(s, ana, pedido(("parlante", "1")), "CUOTAS", 4, D("3.520"), date(2026, 7, 27), vendedor)
    credito.registrar_venta(s, ana, pedido(("detergente", "1")), "FIN_DE_MES", None, None, date(2026, 8, 3), vendedor)
    credito.registrar_venta(s, ana, pedido(("leche", "1"), ("huevos", "1")), "FIN_DE_MES", None, None,
                            date(2026, 9, 2), vendedor)

    for cliente in (juan, ana):
        clientes.nuevo_codigo(s, cliente, vendedor, CODIGOS[cliente.numero_documento])
    return True


def preparar():
    """Crea las tablas y carga los datos de prueba si hace falta."""
    Base.metadata.create_all(motor)
    with Sesion() as s:
        if sembrar(s):
            s.commit()


if __name__ == "__main__":
    if "--reiniciar" in sys.argv and RUTA_BD.exists():
        RUTA_BD.unlink()
        print(f"Base de datos eliminada: {RUTA_BD}")
    preparar()
    print(f"Listo. Vendedor: {USUARIO} / {CLAVE}. Códigos del portal: {', '.join(CODIGOS.values())}")
