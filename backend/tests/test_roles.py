"""Roles de usuario, baja de tiendas y datos que el vendedor y el cliente ven de cada pago."""
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.bd import Base, Sesion, motor
from app.main import app
from app.semilla import CLAVE, CODIGOS, DUENO, SUPERADMIN, USUARIO, sembrar
from app.servicios import sistema

HOY = date(2026, 9, 30)
CLAVE_LARGA = "clave-larga-1234"
TIENDA_NUEVA = {"nombre": "Minimarket Sol", "giro": "Minimarket",
                "admin_usuario": "dueno_sol", "admin_clave": CLAVE_LARGA}


@pytest.fixture
def c(monkeypatch):
    """Base recién sembrada (tienda 1 con su vendedor, dueño y superadmin) y fecha fija."""
    Base.metadata.drop_all(motor)
    Base.metadata.create_all(motor)
    with Sesion() as s:
        sembrar(s)
        s.commit()
    monkeypatch.setattr(sistema, "fecha_real", lambda: HOY)
    with TestClient(app) as cliente:
        yield cliente


def entrar(c, usuario, clave=CLAVE):
    r = c.post("/api/auth/login", json={"usuario": usuario, "clave": clave})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def tienda_con_dueno(c):
    """El superadmin crea una segunda tienda; devuelve su id y los encabezados de su dueño."""
    r = c.post("/api/superadmin/tiendas", json=TIENDA_NUEVA, headers=entrar(c, SUPERADMIN))
    assert r.status_code == 201, r.text
    return r.json()["tienda"]["id"], entrar(c, "dueno_sol", CLAVE_LARGA)


def test_cada_rol_solo_entra_a_lo_suyo(c):
    super_, dueno, vendedor = entrar(c, SUPERADMIN), entrar(c, DUENO), entrar(c, USUARIO)
    assert c.get("/api/superadmin/tiendas", headers=super_).status_code == 200
    assert c.get("/api/superadmin/tiendas", headers=dueno).status_code == 403
    assert c.get("/api/admin/vendedores", headers=dueno).status_code == 200
    assert c.get("/api/admin/vendedores", headers=vendedor).status_code == 403
    assert c.get("/api/clientes", headers=vendedor).status_code == 200
    assert c.get("/api/clientes", headers=dueno).status_code == 403
    assert c.get("/api/clientes", headers=super_).status_code == 403


def test_el_superadmin_crea_la_tienda_y_su_dueno_registra_vendedores(c):
    tienda_id, dueno = tienda_con_dueno(c)
    assert c.post("/api/superadmin/tiendas", json=TIENDA_NUEVA, headers=entrar(c, SUPERADMIN)).status_code == 409
    corta = c.post("/api/admin/vendedores", json={"usuario": "caja1", "clave": "corta"}, headers=dueno)
    assert corta.status_code == 422
    r = c.post("/api/admin/vendedores", json={"usuario": "caja1", "clave": CLAVE_LARGA}, headers=dueno)
    assert r.status_code == 201 and r.json()["tienda_id"] == tienda_id
    caja = entrar(c, "caja1", CLAVE_LARGA)
    assert c.get("/api/clientes", headers=caja).json() == []  # tienda nueva: no ve los clientes de otra


def test_una_tienda_no_ve_ni_toca_lo_de_otra(c):
    _, dueno = tienda_con_dueno(c)
    assert c.get("/api/admin/clientes", headers=dueno).json() == []
    assert c.get("/api/admin/clientes/1", headers=dueno).status_code == 404
    vendedor_ajeno = c.get("/api/admin/vendedores", headers=entrar(c, DUENO)).json()[0]["id"]
    assert c.patch(f"/api/admin/vendedores/{vendedor_ajeno}", json={"activo": False}, headers=dueno).status_code == 404
    assert c.put(f"/api/admin/vendedores/{vendedor_ajeno}/clave", json={"clave": CLAVE_LARGA}, headers=dueno).status_code == 404


def test_un_vendedor_desactivado_pierde_el_acceso_al_instante(c):
    dueno, vendedor = entrar(c, DUENO), entrar(c, USUARIO)
    vendedor_id = c.get("/api/admin/vendedores", headers=dueno).json()[0]["id"]
    assert c.patch(f"/api/admin/vendedores/{vendedor_id}", json={"activo": False}, headers=dueno).status_code == 200
    assert c.get("/api/clientes", headers=vendedor).status_code == 401
    assert c.post("/api/auth/login", json={"usuario": USUARIO, "clave": CLAVE}).status_code == 401


def test_la_baja_de_la_tienda_cierra_sesiones_y_bloquea_el_portal(c):
    super_, vendedor, dueno = entrar(c, SUPERADMIN), entrar(c, USUARIO), entrar(c, DUENO)
    assert c.get("/api/clientes", headers=vendedor).status_code == 200

    r = c.patch("/api/superadmin/tiendas/1/estado", json={"activa": False}, headers=super_)
    assert r.status_code == 200 and r.json()["estado"] == "INACTIVA"
    for sesion_abierta in (vendedor, dueno):
        assert c.get("/api/clientes" if sesion_abierta is vendedor else "/api/admin/vendedores",
                     headers=sesion_abierta).status_code == 401
    assert c.post("/api/auth/login", json={"usuario": USUARIO, "clave": CLAVE}).status_code == 403
    assert c.post("/api/portal", json={"codigo": CODIGOS["45781236"]}).status_code == 403

    c.patch("/api/superadmin/tiendas/1/estado", json={"activa": True}, headers=super_)
    assert c.get("/api/clientes", headers=vendedor).status_code == 200
    assert c.post("/api/portal", json={"codigo": CODIGOS["45781236"]}).status_code == 200


def test_cambiar_y_restablecer_claves(c):
    vendedor = entrar(c, USUARIO)
    mala = c.put("/api/auth/clave", json={"clave_actual": "otra", "clave_nueva": CLAVE_LARGA}, headers=vendedor)
    assert mala.status_code == 400
    ok = c.put("/api/auth/clave", json={"clave_actual": CLAVE, "clave_nueva": CLAVE_LARGA}, headers=vendedor)
    assert ok.status_code == 200
    assert c.post("/api/auth/login", json={"usuario": USUARIO, "clave": CLAVE}).status_code == 401
    entrar(c, USUARIO, CLAVE_LARGA)

    dueno = entrar(c, DUENO)
    vendedor_id = c.get("/api/admin/vendedores", headers=dueno).json()[0]["id"]
    nueva = "otra-clave-9876"
    assert c.put(f"/api/admin/vendedores/{vendedor_id}/clave", json={"clave": nueva}, headers=dueno).status_code == 200
    entrar(c, USUARIO, nueva)

    super_ = entrar(c, SUPERADMIN)
    admin_id = c.get("/api/superadmin/tiendas/1/administradores", headers=super_).json()[0]["id"]
    assert c.put(f"/api/superadmin/tiendas/1/administradores/{admin_id}/clave",
                 json={"clave": nueva}, headers=super_).status_code == 200
    entrar(c, DUENO, nueva)


def test_el_estado_de_cuenta_pagado_muestra_si_se_pago_con_atraso(c):
    vendedor = entrar(c, USUARIO)
    juan = next(x for x in c.get("/api/clientes", headers=vendedor).json() if x["numero_documento"] == "45781236")
    pagados = [e for e in c.get(f"/api/clientes/{juan['id']}", headers=vendedor).json()["estados_cuenta"]
               if e["estado"] == "PAGADO" and e["pago"]]
    puntuales = [e for e in pagados if e["pago"]["dias_mora"] == 0]
    atrasados = [e for e in pagados if e["pago"]["dias_mora"] > 0]
    assert puntuales and len(atrasados) == 1
    tarde = atrasados[0]["pago"]
    assert float(tarde["recargo_mora"]) > 0
    assert float(tarde["total"]) == pytest.approx(float(tarde["exigible"]) + float(tarde["recargo_mora"]))
    assert all(float(e["pago"]["recargo_mora"]) == 0 for e in puntuales)


def test_ventas_y_pagos_indican_quien_los_registro(c):
    vendedor = entrar(c, USUARIO)
    assert all(v["registrado_por"] == USUARIO for v in c.get("/api/ventas", headers=vendedor).json())
    assert all(p["registrado_por"] == USUARIO for p in c.get("/api/pagos", headers=vendedor).json())


def test_el_portal_no_muestra_quien_registro_cada_cosa(c):
    r = c.post("/api/portal", json={"codigo": CODIGOS["45781236"]}).json()
    assert r["ventas"] and r["pagos"]
    assert all(x["registrado_por"] is None for x in r["ventas"] + r["pagos"])
