"""Aplicación FastAPI de FiaMe. Ejecutar: uvicorn app.main:app --reload"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

from app import rutas_portal, rutas_vendedor, rutas_auth, rutas_superadmin, rutas_admin, rutas_admin_clientes
from app.dominio import ReglaDeNegocio
from app.rutas import router
from app.semilla import preparar


@asynccontextmanager
async def ciclo_de_vida(_: FastAPI):
    preparar()
    yield


app = FastAPI(
    title="FiaMe API",
    description="Cálculo de créditos de tiendas de barrio: tasas, ventas, cronogramas, estados de cuenta y pagos.",
    version="0.2.0",
    lifespan=ciclo_de_vida,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5180", "http://127.0.0.1:5180"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ReglaDeNegocio)
def regla_de_negocio(_: Request, error: ReglaDeNegocio):
    """Una operación rechazada por una regla de negocio no es un error del sistema."""
    return JSONResponse(status_code=400, content={"detail": str(error)})


app.include_router(router)
app.include_router(rutas_auth.router)
app.include_router(rutas_superadmin.router)
app.include_router(rutas_admin.router)
app.include_router(rutas_admin_clientes.router)
app.include_router(rutas_vendedor.router)
app.include_router(rutas_portal.router)


@app.get("/", include_in_schema=False)
def inicio():
    return RedirectResponse("/docs")
