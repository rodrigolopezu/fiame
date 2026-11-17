
"""Roles internos de FiaMe. Los clientes se almacenan en la tabla cliente."""
from enum import Enum


class RolUsuario(str, Enum):
    SUPERADMIN = "SUPERADMIN"
    ADMIN = "ADMIN"
    VENDEDOR = "VENDEDOR"


ROLES_VALIDOS = frozenset(rol.value for rol in RolUsuario)

ROLES_CON_TIENDA = frozenset({
    RolUsuario.ADMIN.value,
    RolUsuario.VENDEDOR.value
})


def validar_rol_y_tienda(
    rol: str,
    tienda_id: int | None
) -> None:
    """Validación de negocio para creación y actualización de usuarios."""

    if rol not in ROLES_VALIDOS:
        raise ValueError(f"Rol no permitido: {rol}")

    if rol == RolUsuario.SUPERADMIN.value and tienda_id is not None:
        raise ValueError("SUPERADMIN no debe pertenecer a una tienda")

    if rol in ROLES_CON_TIENDA and (
        tienda_id is None or tienda_id <= 0
    ):
        raise ValueError(
            "ADMIN y VENDEDOR deben pertenecer a una tienda válida"
        )
