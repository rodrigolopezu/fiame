"""Casos de prueba de docs/casos-de-prueba.md y reglas de negocio, a través de la API."""
import pytest
from fastapi.testclient import TestClient

from app.main import app

cliente = TestClient(app)


def tasa(tipo, valor, periodo="ANUAL", cap=None):
    return {"tipo": tipo, "periodo": periodo, "valor": valor, "capitalizacion": cap}


def venta(fecha, *items, modalidad="FIN_DE_MES", cuotas=None, tc=None):
    return {"tipo": "VENTA", "fecha": fecha, "modalidad": modalidad, "numero_cuotas": cuotas,
            "tipo_cambio": tc, "items": list(items)}


def item(descripcion, precio, moneda="PEN", cantidad="1", **permisos):
    return {"descripcion": descripcion, "precio_lista": precio, "moneda": moneda, "cantidad": cantidad, **permisos}


def pago(fecha, k=1):
    return {"tipo": "PAGO", "fecha": fecha, "cantidad_estados": k}


def simular(condiciones, eventos, hasta):
    r = cliente.post("/api/simular", json={"condiciones": condiciones, "eventos": eventos, "fecha_hasta": hasta})
    assert r.status_code == 200, r.text
    return r.json()


def ec(res, codigo):
    return next(x for x in res["estados_cuenta"] if x["codigo"] == codigo)


CASO_1 = {
    "moneda": "PEN", "limite_credito": "500.00", "max_meses": 3, "dia_corte": 20, "dia_pago": 26,
    "tasa_compensatoria": tasa("EFECTIVA", "24"), "tasa_moratoria": tasa("EFECTIVA", "36"),
}

EVENTOS_CASO_1 = [
    venta("2026-09-10", item("Arroz 5 kg", "22.00")),
    venta("2026-09-15", item("Licuadora", "165.00"), modalidad="CUOTAS", cuotas=3),
    venta("2026-09-22", item("Arroz 5 kg", "22.00")),
    venta("2026-09-28", item("Gaseosa 3 L", "12.00")),
    pago("2026-09-30"),
    venta("2026-10-16", item("Televisor", "400.00")),
    venta("2026-10-18", item("Aceite 1 L", "9.50")),
    pago("2026-10-24"),
    pago("2026-11-26"),
    pago("2026-12-26"),
]


@pytest.fixture(scope="module")
def caso_1():
    return simular(CASO_1, EVENTOS_CASO_1, "2026-12-31")


def test_caso_1_tasas(caso_1):
    assert caso_1["tasa_compensatoria"]["tea"] == "24.0000000"
    assert caso_1["tasa_compensatoria"]["tem"] == "1.8087582"


def test_caso_1_cronograma_licuadora(caso_1):
    licuadora = caso_1["ventas"][1]
    assert (licuadora["dias"], licuadora["tasa_periodo"], licuadora["total"]) == (11, "0.6594496", "166.09")
    filas = [(c["fecha_vencimiento"], c["saldo_inicial"], c["interes"], c["cuota"], c["amortizacion"],
              c["saldo_final"], c["libera_linea"]) for c in licuadora["cuotas"]]
    assert filas == [
        ("2026-10-26", "166.09", "3.00", "57.38", "54.38", "111.71", "54.38"),
        ("2026-11-26", "111.71", "2.02", "57.37", "55.35", "56.36", "55.35"),
        ("2026-12-26", "56.36", "1.02", "57.38", "56.36", "0.00", "55.27"),
    ]


def test_caso_1_estado_septiembre_y_pago_con_mora(caso_1):
    septiembre = ec(caso_1, "EC-2026-09")
    assert (septiembre["fecha_pago"], septiembre["total_a_pagar"]) == ("2026-09-26", "22.21")
    linea = septiembre["lineas"][0]
    assert (linea["dias"], linea["tasa"], linea["interes"]) == (16, "0.9606353", "0.21")
    p = caso_1["pagos"][0]["detalle"][0]
    assert (p["dias_mora"], p["tasa_compensatoria_mora"], p["interes_compensatorio_mora"]) == (4, "0.2392985", "0.05")
    assert (p["tasa_moratoria"], p["interes_moratorio"], p["total"]) == ("0.3422340", "0.08", "22.34")
    assert (p["mora"], p["interes"], p["capital"]) == ("0.08", "0.26", "22.00")


def test_caso_1_rechazos(caso_1):
    rechazos = {r["evento"]: r["mensaje"] for r in caso_1["bitacora"] if r["resultado"] == "RECHAZADO"}
    assert set(rechazos) == {3, 5}
    assert "vencidos: EC-2026-09" in rechazos[3]
    assert "S/ 313.00" in rechazos[5]


def test_caso_1_estado_octubre_y_pago_anticipado(caso_1):
    octubre = ec(caso_1, "EC-2026-10")
    assert [(l["descripcion"], l["dias"], l["tasa"], l["total"]) for l in octubre["lineas"]] == [
        ("Licuadora", None, "1.8087582", "57.38"),
        ("Arroz 5 kg", 34, "2.0523851", "22.45"),
        ("Aceite 1 L", 8, "0.4791697", "9.55"),
    ]
    assert (octubre["total_capital"], octubre["total_interes"], octubre["total_a_pagar"]) == ("85.88", "3.50", "89.38")
    p = caso_1["pagos"][1]
    assert (p["total"], p["total_mora"], p["linea_liberada"]) == ("89.38", "0.00", "85.88")


def test_caso_1_linea_de_credito(caso_1):
    lineas = [(r["fecha"], r["linea"]["disponible"]) for r in caso_1["bitacora"] if r["resultado"] == "OK"
              and r["tipo"] != "CORTE"]
    assert lineas == [
        ("2026-09-10", "478.00"), ("2026-09-15", "313.00"), ("2026-09-22", "291.00"),
        ("2026-09-30", "313.00"), ("2026-10-18", "303.50"), ("2026-10-24", "389.38"),
        ("2026-11-26", "444.73"), ("2026-12-26", "500.00"),
    ]
    assert ec(caso_1, "EC-2026-12")["total_a_pagar"] == "57.38"
    assert [v["estado"] for v in caso_1["ventas"]] == ["PAGADA"] * 4


CASO_2 = {
    "moneda": "PEN", "limite_credito": "800.00", "max_meses": 6, "dia_corte": 25, "dia_pago": 5,
    "tasa_compensatoria": tasa("NOMINAL", "30", cap="MENSUAL"),
    "tasa_moratoria": tasa("NOMINAL", "36", cap="DIARIA"),
}

EVENTOS_CASO_2 = [
    venta("2026-09-26", item("Kit importado", "49.90", "USD"), modalidad="CUOTAS", cuotas=4, tc="3.520"),
    venta("2026-10-03", item("Limpieza facial", "80.00")),
    venta("2026-10-25", item("Labial", "35.00")),
    pago("2026-11-03"),
    pago("2026-12-15"),
]


@pytest.fixture(scope="module")
def caso_2():
    return simular(CASO_2, EVENTOS_CASO_2, "2026-12-31")


def test_caso_2_tasas_nominales(caso_2):
    assert caso_2["tasa_compensatoria"]["tea"] == "34.4888824"
    assert caso_2["tasa_compensatoria"]["tem"] == "2.5000000"
    assert caso_2["tasa_moratoria"]["tea"] == "43.3071610"


def test_caso_2_kit_en_dolares(caso_2):
    kit = caso_2["ventas"][0]
    assert (kit["capital"], kit["fecha_pago"], kit["dias"], kit["tasa_periodo"], kit["total"]) == (
        "175.65", "2026-11-05", 40, "3.3471459", "181.53")
    assert [(c["fecha_vencimiento"], c["interes"], c["cuota"], c["saldo_final"]) for c in kit["cuotas"]] == [
        ("2026-12-05", "4.54", "48.25", "137.82"),
        ("2027-01-05", "3.45", "48.26", "93.01"),
        ("2027-02-05", "2.33", "48.26", "47.08"),
        ("2027-03-05", "1.18", "48.26", "0.00"),
    ]


def test_caso_2_estado_octubre_incluye_compra_del_dia_de_corte(caso_2):
    octubre = ec(caso_2, "EC-2026-10")
    assert octubre["fecha_pago"] == "2026-11-05"
    assert [(l["descripcion"], l["dias"], l["tasa"], l["total"]) for l in octubre["lineas"]] == [
        ("Limpieza facial", 33, "2.7534120", "82.20"),
        ("Labial", 11, "0.9095069", "35.32"),
    ]
    assert octubre["total_a_pagar"] == "117.52"
    assert caso_2["pagos"][0]["total"] == "117.52"


def test_caso_2_cuota_pagada_con_mora(caso_2):
    assert ec(caso_2, "EC-2026-11")["total_a_pagar"] == "48.25"
    p = caso_2["pagos"][1]["detalle"][0]
    assert (p["dias_mora"], p["tasa_compensatoria_mora"], p["interes_compensatorio_mora"]) == (10, "0.8264838", "0.40")
    assert (p["tasa_moratoria"], p["interes_moratorio"], p["total"]) == ("1.0045120", "0.48", "49.13")
    assert (p["mora"], p["interes"], p["capital"]) == ("0.48", "4.94", "43.71")
    assert caso_2["linea"]["disponible"] == "668.06"
    assert ec(caso_2, "EC-2026-12")["estado"] == "PENDIENTE"


# ---------------------------------------------------------------- Reglas de negocio

BASE = {**CASO_1, "max_meses": 6}


def test_estado_de_cuenta_sin_deuda_nace_pagado():
    res = simular(BASE, [venta("2026-10-10", item("Pan", "5.00")), pago("2026-10-26")], "2026-11-30")
    assert ec(res, "EC-2026-10")["estado"] == "PAGADO"
    noviembre = ec(res, "EC-2026-11")
    assert (noviembre["total_a_pagar"], noviembre["estado"], noviembre["pagado_con"]) == ("0.00", "PAGADO", None)


def test_estado_vencido_muestra_deuda_al_dia():
    res = simular(BASE, [venta("2026-09-10", item("Arroz", "22.00"))], "2026-09-30")
    septiembre = ec(res, "EC-2026-09")
    assert septiembre["estado"] == "VENCIDO"
    assert septiembre["deuda_al_dia"]["dias_mora"] == 4
    assert septiembre["deuda_al_dia"]["total_a_pagar"] == "22.34"


def test_sin_bloqueo_por_vencido_permite_vender():
    res = simular({**BASE, "bloquear_con_vencido": False},
                  [venta("2026-09-10", item("Arroz", "22.00")), venta("2026-09-28", item("Pan", "5.00"))],
                  "2026-09-30")
    assert all(r["resultado"] == "OK" for r in res["bitacora"])


def test_anular_venta_antes_y_despues_del_corte():
    res = simular(BASE, [
        venta("2026-09-10", item("Arroz", "22.00")),
        venta("2026-09-12", item("Leche", "4.50")),
        {"tipo": "ANULAR_VENTA", "fecha": "2026-09-13", "venta": 2},
        {"tipo": "ANULAR_VENTA", "fecha": "2026-09-21", "venta": 1},
    ], "2026-09-25")
    resultados = [r["resultado"] for r in res["bitacora"] if r["tipo"] == "ANULAR_VENTA"]
    assert resultados == ["OK", "RECHAZADO"]
    assert ec(res, "EC-2026-09")["total_a_pagar"] == "22.21"
    assert res["linea"]["usado"] == "22.00"


def test_cambio_de_tasa_solo_afecta_ventas_siguientes():
    res = simular(BASE, [
        venta("2026-09-10", item("Arroz", "22.00")),
        {"tipo": "CAMBIO_CONDICIONES", "fecha": "2026-09-11", "tasa_compensatoria": tasa("EFECTIVA", "48")},
        venta("2026-09-12", item("Arroz", "22.00")),
    ], "2026-09-25")
    primera, segunda = res["ventas"]
    assert primera["tasa_compensatoria"] == "TEA 24 %" and segunda["tasa_compensatoria"] == "TEA 48 %"
    assert ec(res, "EC-2026-09")["tea_compensatoria"] == "48.0000000"


def test_pago_de_dos_estados_en_orden():
    res = simular({**BASE, "bloquear_con_vencido": False}, [
        venta("2026-09-10", item("Arroz", "22.00")),
        venta("2026-10-10", item("Arroz", "22.00")),
        pago("2026-10-26", k=2),
    ], "2026-10-31")
    detalle = res["pagos"][0]["detalle"]
    assert [d["estado_cuenta"] for d in detalle] == ["EC-2026-09", "EC-2026-10"]
    assert [d["dias_mora"] for d in detalle] == [30, 0]


def test_cliente_en_dolares_con_producto_en_soles():
    res = simular({**BASE, "moneda": "USD"},
                  [venta("2026-09-10", item("Licuadora", "176.00"), tc="3.520")], "2026-09-15")
    assert res["ventas"][0]["capital"] == "50.00"


@pytest.mark.parametrize("evento, mensaje", [
    (venta("2026-09-10", item("Kit", "50.00", "USD")), "se requiere el tipo de cambio"),
    (venta("2026-09-10", item("Corte", "20.00", permite_pago_unico=False)), "pago único"),
    (venta("2026-09-10", item("Pan", "5.00", permite_cuotas=False), modalidad="CUOTAS", cuotas=2), "cuotas"),
    (venta("2026-09-10", item("TV", "300.00"), modalidad="CUOTAS", cuotas=7), "entre 1 y 6"),
    (pago("2026-09-10"), "No hay estados de cuenta pendientes"),
])
def test_rechazos(evento, mensaje):
    res = simular(BASE, [evento], "2026-09-15")
    registro = res["bitacora"][0]
    assert registro["resultado"] == "RECHAZADO" and mensaje in registro["mensaje"]


def test_tasa_nominal_sin_capitalizacion_asume_diaria():
    r = cliente.post("/api/calculadora/tasa", json={"tasa": tasa("NOMINAL", "4", "SEMESTRAL"), "dias": 30})
    assert r.json()["tasa_efectiva"] == "0.6688193"  # libro, ej. 4-11


def test_capitalizacion_mayor_que_el_periodo_es_invalida():
    r = cliente.post("/api/calculadora/tasa", json={"tasa": tasa("NOMINAL", "2", "MENSUAL", "TRIMESTRAL")})
    assert r.status_code == 422


def test_calculadoras_devuelven_decimales_como_texto():
    r = cliente.post("/api/calculadora/cronograma", json={
        "capital": "112000", "tasa": tasa("EFECTIVA", "10"), "numero_cuotas": 9, "dias_periodo": 120})
    assert r.json()["filas"][0]["cuota"] == "14537.95"  # libro, ej. 8-1
    r = cliente.post("/api/calculadora/mora", json={
        "exigible": "20000", "tasa_compensatoria": tasa("NOMINAL", "20"),
        "tasa_moratoria": tasa("EFECTIVA", "60"), "dias_mora": 7})
    assert (r.json()["interes_compensatorio"], r.json()["interes_moratorio"]) == ("77.91", "183.62")  # ej. 5-36
    r = cliente.post("/api/calculadora/interes", json={
        "capital": "3000", "tasa": tasa("NOMINAL", "18.5"), "fecha_inicio": "2010-02-14", "fecha_fin": "2011-09-13"})
    assert r.json()["valor_futuro"] == "4033.10"  # ej. 3-3
