"""Respuestas sin pérdida de precisión: los Decimal viajan como texto, nunca como float."""
from decimal import Decimal

from pydantic import BaseModel


def exacto(valor):
    if isinstance(valor, Decimal):
        return str(valor)
    if isinstance(valor, BaseModel):
        return valor.model_dump(mode="json")
    if isinstance(valor, dict):
        return {k: exacto(v) for k, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [exacto(v) for v in valor]
    return valor
