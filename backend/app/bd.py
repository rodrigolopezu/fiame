"""Conexión a la base de datos.

En local se usa SQLite (archivo backend/fiame.db). El tipo `Exacto` guarda los decimales
como texto en SQLite, que no tiene un tipo decimal exacto, y como NUMERIC en PostgreSQL.
"""
import os
from decimal import Decimal
from pathlib import Path

from sqlalchemy import Numeric, String, create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.types import TypeDecorator

RUTA_BD = Path(__file__).resolve().parent.parent / "fiame.db"
URL = os.environ.get("FIAME_BD", f"sqlite:///{RUTA_BD}")

motor = create_engine(URL, connect_args={"check_same_thread": False} if URL.startswith("sqlite") else {})
Sesion = sessionmaker(motor, expire_on_commit=False)


@event.listens_for(motor, "connect")
def _activar_llaves_foraneas(conexion, _):
    if URL.startswith("sqlite"):
        conexion.execute("PRAGMA foreign_keys = ON")


class Base(DeclarativeBase):
    pass


class Exacto(TypeDecorator):
    """Decimal exacto: NUMERIC(p, s) en PostgreSQL y texto en SQLite."""

    impl = String
    cache_ok = True

    def __init__(self, precision: int, escala: int):
        super().__init__()
        self.precision, self.escala = precision, escala

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(Numeric(self.precision, self.escala))
        return dialect.type_descriptor(String(self.precision + 2))

    def process_bind_param(self, valor, dialect):
        if valor is None:
            return None
        valor = Decimal(valor)
        return valor if dialect.name == "postgresql" else str(valor)

    def process_result_value(self, valor, dialect):
        return None if valor is None else Decimal(valor)


def sesion():
    """Dependencia de FastAPI: una sesión por petición."""
    with Sesion() as s:
        yield s
