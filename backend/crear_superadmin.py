"""Inicializa el primer SUPERADMIN sin modificar el esquema ni los registros existentes.
Ejecutar desde la carpeta backend: python crear_superadmin.py
"""
from getpass import getpass
from pathlib import Path
import sys

from sqlalchemy import select

from app.bd import Sesion, motor
from app.modelos import Usuario
from app.servicios.seguridad import hash_clave


def main():
    if motor.url.get_backend_name() == 'sqlite':
        archivo = Path(motor.url.database).resolve()
        if not archivo.is_file():
            sys.exit(f'ERROR: no existe la base SQLite: {archivo}. No se creará una base vacía.')

    with Sesion() as s:
        existentes = s.scalars(select(Usuario).where(Usuario.rol == 'SUPERADMIN')).all()
        if existentes:
            sys.exit('Ya existe un SUPERADMIN. No se creó otra cuenta.')

        nombre = input('Nombre del primer superadministrador: ').strip()
        if not 3 <= len(nombre) <= 60 or not nombre.isascii() or not all(c.isalnum() or c in '._-' for c in nombre):
            sys.exit('Nombre inválido: 3-60 caracteres ASCII, letras, números, punto, guion o guion bajo.')
        if s.scalar(select(Usuario.id).where(Usuario.usuario == nombre)) is not None:
            sys.exit('Ese nombre de usuario ya existe. No se modificó ninguna cuenta.')

        clave = getpass('Contraseña (mínimo 12 caracteres): ')
        confirmacion = getpass('Repite la contraseña: ')
        if len(clave) < 12 or clave != confirmacion:
            sys.exit('Contraseña inválida o no coincide. No se creó la cuenta.')

        cuenta = Usuario(usuario=nombre, password_hash=hash_clave(clave), rol='SUPERADMIN', tienda_id=None, activo=True)
        s.add(cuenta)
        try:
            s.commit()
        except Exception:
            s.rollback()
            raise
        print(f'SUPERADMIN creado correctamente (ID {cuenta.id}). No se muestra ni almacena la contraseña en claro.')


if __name__ == '__main__':
    main()
