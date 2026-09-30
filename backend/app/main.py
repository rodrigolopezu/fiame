"""Aplicación FastAPI de FiaMe. Ejecutar: uvicorn app.main:app --reload"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.rutas import router

app = FastAPI(
    title="FiaMe API",
    description="Cálculo de créditos de tiendas de barrio: tasas, ventas, cronogramas, estados de cuenta y pagos.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5180", "http://127.0.0.1:5180"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/", include_in_schema=False)
def inicio():
    return RedirectResponse("/docs")
