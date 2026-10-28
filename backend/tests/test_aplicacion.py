"""Aplicación del vendedor y portal del cliente, sobre la base de datos de prueba."""
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.bd import Base, Sesion, motor
from app.main import app
from app.semilla import CLAVE, CODIGOS, USUARIO, sembrar
from app.servicios import sistema

HOY = date(2026, 9, 30)


@pytest.fixture
def cliente(monkeypatch):
    """Base recién sembrada y fecha del sistema fija en el 30/09/2026."""
    Base.metadata.drop_all(motor)
    Base.metadata.create_all(motor)
    with Sesion() as s:
        sembrar(s)
        s.commit()
    monkeypatch.setattr(sistema, "fecha_real", lambda: HOY)
    with TestClient(app) as c:
        token = c.post("/api/auth/login", json={"usuario": USUARIO, "clave": CLAVE}).json()["token"]
        c.headers["Authorization"] = f"Bearer {token}"
        yield c


def simular(condiciones, eventos):
    r = TestClient(app).post("/api/simular", json={"condiciones": condiciones, "eventos": eventos,
                                                    "fecha_hasta": HOY.isoformat()})
    assert r.status_code == 200, r.text
    return r.json()


def item(descripcion, precio, cantidad="1", moneda="PEN"):
    return {"descripcion": descripcion, "precio_lista": precio, "cantidad": cantidad, "moneda": moneda}


def por_cliente(c, documento):
    fila = next(x for x in c.get("/api/clientes").json() if x["numero_documento"] == documento)
    return c.get(f"/api/clientes/{fila['id']}").json()


def resumen_estados(estados):
    """Estados de cuenta con deuda. Los de S/ 0.00 dependen de desde cuándo existe el cliente:
    la aplicación genera cortes desde el alta; el simulador, desde el primer evento."""
    return sorted((e["codigo"], e["total_a_pagar"], e["estado"]) for e in estados if e["total_a_pagar"] != "0.00")


# ---------------------------------------------------------------- Coincidencia con el simulador

def test_historial_de_juan_coincide_con_el_simulador(cliente):
    juan = por_cliente(cliente, "45781236")
    sim = simular({
        "moneda": "PEN", "limite_credito": "500.00", "max_meses": 3, "dia_corte": 20, "dia_pago": 26,
        "tasa_compensatoria": {"tipo": "EFECTIVA", "valor": "24"},
        "tasa_moratoria": {"tipo": "EFECTIVA", "valor": "36"},
    }, [
        {"tipo": "VENTA", "fecha": "2026-07-10", "items": [item("Arroz", "22.00")]},
        {"tipo": "VENTA", "fecha": "2026-07-15", "items": [item("Licuadora", "165.00")],
         "modalidad": "CUOTAS", "numero_cuotas": 3},
        {"tipo": "PAGO", "fecha": "2026-07-25"},
        {"tipo": "VENTA", "fecha": "2026-08-05", "items": [item("Aceite", "9.50", "2"), item("Azúcar", "4.50", "2")]},
        {"tipo": "PAGO", "fecha": "2026-08-29"},
        {"tipo": "VENTA", "fecha": "2026-09-12", "items": [item("Fideos", "5.80", "3"), item("Atún", "17.70")]},
        {"tipo": "VENTA", "fecha": "2026-09-24", "items": [item("Gaseosa", "12.00", "2")]},
        {"tipo": "PAGO", "fecha": "2026-09-26"},
    ])
    assert resumen_estados(juan["estados_cuenta"]) == resumen_estados(sim["estados_cuenta"])
    assert [p["total"] for p in reversed(juan["pagos"])] == [p["total"] for p in sim["pagos"]]
    assert [p["total_mora"] for p in reversed(juan["pagos"])] == ["0.00", "0.22", "0.00"]
    assert juan["linea"] == sim["linea"]
    licuadora = next(v for v in juan["ventas"] if v["modalidad"] == "CUOTAS")
    assert [c["cuota"] for c in licuadora["cuotas"]] == [c["cuota"] for c in sim["ventas"][1]["cuotas"]]
    assert juan["score"]["semaforo"] == "VERDE"


def test_historial_de_ana_coincide_con_el_simulador(cliente):
    ana = por_cliente(cliente, "70412589")
    sim = simular({
        "moneda": "PEN", "limite_credito": "800.00", "max_meses": 6, "dia_corte": 25, "dia_pago": 5,
        "tasa_compensatoria": {"tipo": "NOMINAL", "valor": "30", "capitalizacion": "MENSUAL"},
        "tasa_moratoria": {"tipo": "NOMINAL", "valor": "36", "capitalizacion": "DIARIA"},
    }, [
        {"tipo": "VENTA", "fecha": "2026-07-27", "items": [item("Parlante", "49.90", moneda="USD")],
         "modalidad": "CUOTAS", "numero_cuotas": 4, "tipo_cambio": "3.520"},
        {"tipo": "VENTA", "fecha": "2026-08-03", "items": [item("Detergente", "29.90")]},
        {"tipo": "VENTA", "fecha": "2026-09-02", "items": [item("Leche", "24.00"), item("Huevos", "18.00")]},
    ])
    assert resumen_estados(ana["estados_cuenta"]) == resumen_estados(sim["estados_cuenta"])
    vencido = next(e for e in ana["estados_cuenta"] if e["estado"] == "VENCIDO")
    esperado = next(e for e in sim["estados_cuenta"] if e["estado"] == "VENCIDO")
    assert vencido["deuda_al_dia"] == esperado["deuda_al_dia"]
    assert vencido["codigo"] == "EC-2026-08" and vencido["deuda_al_dia"]["dias_mora"] == 25
    assert vencido["deuda_al_dia"]["recargo"] == "1.42"  # 32.14 − 30.72
    assert ana["score"]["semaforo"] == "ROJO"
    assert ana["ventas"][-1]["capital"] == "175.65"  # US$ 49.90 × 3.520


# ---------------------------------------------------------------- Flujo del vendedor

def test_login_rechaza_clave_incorrecta():
    with TestClient(app) as c:
        assert c.post("/api/auth/login", json={"usuario": USUARIO, "clave": "mala"}).status_code == 401
        assert c.get("/api/clientes").status_code == 401


def test_catalogo_de_prueba_tiene_12_productos(cliente):
    productos = cliente.get("/api/productos").json()
    assert len(productos) == 12
    assert sum(p["permite_cuotas"] for p in productos) == 2
    assert {p["moneda"] for p in productos} == {"PEN", "USD"}


NUEVO = {
    "nombres": "Luis", "apellidos": "Ramos", "tipo_documento": "DNI", "numero_documento": "41234567",
    "telefono": "999888777", "moneda": "PEN", "limite_credito": "300.00", "max_meses": 3,
    "dia_corte": 20, "dia_pago": 26,
    "tasa_compensatoria": {"tipo": "EFECTIVA", "periodo": "ANUAL", "valor": "24"},
    "tasa_moratoria": {"tipo": "EFECTIVA", "periodo": "ANUAL", "valor": "36"},
}


def test_flujo_completo_de_un_cliente_nuevo(cliente):
    luis = cliente.post("/api/clientes", json=NUEVO).json()
    arroz = next(p for p in cliente.get("/api/productos").json() if p["nombre"].startswith("Arroz"))
    venta = {"cliente_id": luis["id"], "items": [{"producto_id": arroz["id"], "cantidad": "2"}]}

    previa = cliente.post("/api/ventas/previsualizar", json=venta).json()
    assert (previa["capital"], previa["fecha_pago"]) == ("44.00", "2026-10-26")
    assert cliente.get(f"/api/clientes/{luis['id']}").json()["ventas"] == []  # la vista previa no guarda

    cliente.post("/api/ventas", json=venta)
    excede = cliente.post("/api/ventas", json={**venta, "items": [{"producto_id": arroz["id"], "cantidad": "20"}]})
    assert excede.status_code == 400 and "excede el crédito disponible" in excede.json()["detail"]

    cliente.post("/api/sistema/fecha", json={"fecha": "2026-10-21"})  # pasa el corte del 20/10
    detalle = cliente.get(f"/api/clientes/{luis['id']}").json()
    octubre = next(e for e in detalle["estados_cuenta"] if e["codigo"] == "EC-2026-10")
    assert octubre["estado"] == "PENDIENTE" and octubre["total_capital"] == "44.00"

    liquidacion = cliente.get(f"/api/clientes/{luis['id']}/liquidacion?cantidad=1").json()
    assert liquidacion["total"] == octubre["total_a_pagar"]
    pago = cliente.post("/api/pagos", json={"cliente_id": luis["id"], "cantidad_estados": 1}).json()
    assert pago["total"] == octubre["total_a_pagar"]
    assert cliente.get(f"/api/clientes/{luis['id']}").json()["linea"]["disponible"] == "300.00"

    anulado = cliente.post(f"/api/pagos/{pago['numero']}/anular", json={"motivo": "Error de registro"}).json()
    assert anulado["estado"] == "ANULADO"
    despues = cliente.get(f"/api/clientes/{luis['id']}").json()
    assert despues["linea"]["usado"] == "44.00" and despues["estados_cuenta"][0]["estado"] == "PENDIENTE"


def test_no_se_anula_una_venta_ya_cobrada(cliente):
    juan = por_cliente(cliente, "45781236")
    licuadora = next(v for v in juan["ventas"] if v["modalidad"] == "CUOTAS")  # vigente, cuotas ya cobradas
    r = cliente.post(f"/api/ventas/{licuadora['numero']}/anular")
    assert r.status_code == 400 and "ya fue incluida" in r.json()["detail"]


def test_venta_bloqueada_por_estado_vencido(cliente):
    ana = por_cliente(cliente, "70412589")
    arroz = next(p for p in cliente.get("/api/productos").json() if p["nombre"].startswith("Arroz"))
    r = cliente.post("/api/ventas", json={"cliente_id": ana["id"], "items": [{"producto_id": arroz["id"], "cantidad": "1"}]})
    assert r.status_code == 400 and "EC-2026-08" in r.json()["detail"]


def test_no_cambia_el_ciclo_con_deuda(cliente):
    juan = por_cliente(cliente, "45781236")
    datos = {**NUEVO, "nombres": "Juan", "apellidos": "Pérez Quispe", "numero_documento": "45781236",
             "limite_credito": "500.00", "dia_corte": 15}
    r = cliente.put(f"/api/clientes/{juan['id']}", json=datos)
    assert r.status_code == 400 and "días de corte" in r.json()["detail"]


def test_panel(cliente):
    panel = cliente.get("/api/panel").json()
    assert panel["clientes_activos"] == 2
    assert [v["codigo"] for v in panel["vencidos"]] == ["EC-2026-08"]
    assert panel["clientes"][0]["score"]["semaforo"] == "ROJO"


# ---------------------------------------------------------------- Portal del cliente

@pytest.mark.parametrize("codigo", list(CODIGOS.values()))
def test_portal_con_codigo(cliente, codigo):
    r = TestClient(app).post("/api/portal", json={"codigo": codigo.lower().replace("-", " ")})
    assert r.status_code == 200
    datos = r.json()
    assert datos["estados_cuenta"] and "score" not in datos and "score" not in datos["cliente"]


def test_portal_rechaza_codigo_invalido(cliente):
    assert TestClient(app).post("/api/portal", json={"codigo": "XXXX-XXXX"}).status_code == 404


def test_regenerar_codigo_invalida_el_anterior(cliente):
    juan = por_cliente(cliente, "45781236")
    nuevo = cliente.post(f"/api/clientes/{juan['id']}/codigo").json()["codigo"]
    assert TestClient(app).post("/api/portal", json={"codigo": CODIGOS["45781236"]}).status_code == 404
    assert TestClient(app).post("/api/portal", json={"codigo": nuevo}).status_code == 200


def test_peticiones_simultaneas_no_duplican_cortes(cliente):
    """Al abrir una pantalla llegan varias peticiones a la vez y todas quieren generar el corte."""
    from concurrent.futures import ThreadPoolExecutor

    cliente.post("/api/sistema/fecha", json={"fecha": "2026-11-30"})
    rutas = ["/api/sesion", "/api/panel", "/api/clientes", "/api/estados-cuenta"] * 3
    with ThreadPoolExecutor(max_workers=8) as grupo:
        codigos = list(grupo.map(lambda ruta: cliente.get(ruta).status_code, rutas))
    assert codigos == [200] * len(rutas)
    estados = cliente.get("/api/estados-cuenta").json()
    claves = [(e["cliente_id"], e["codigo"]) for e in estados]
    assert len(claves) == len(set(claves))
