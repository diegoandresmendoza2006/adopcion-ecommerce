"""Prepara una base NUEVA (por ejemplo la de la nube): crea los 4 roles y un administrador.

Uso (desde la carpeta backend, con el venv activo y DATABASE_URL apuntando a esa base):
    python scripts/crear_admin.py

Se puede ejecutar varias veces: no duplica los roles y avisa si el correo ya existe.
"""
import getpass
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import models, security          # noqa: E402  (necesitan el sys.path de arriba)
from app.database import SessionLocal     # noqa: E402

ROLES = {1: "Administrador", 2: "Encargado", 3: "Usuario", 4: "Invitado"}


def main() -> None:
    db = SessionLocal()
    try:
        for rol_id, nombre in ROLES.items():
            if not db.get(models.Rol, rol_id):
                db.add(models.Rol(id=rol_id, nombre=nombre))
        db.commit()
        print("Roles listos:", ", ".join(ROLES.values()))

        nombre = input("Nombre completo del administrador: ").strip()
        email = input("Correo del administrador: ").strip().lower()
        if len(nombre) < 2 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            sys.exit("Nombre o correo no válidos.")
        if db.query(models.Usuario).filter(models.Usuario.email == email).first():
            sys.exit("Ese correo ya existe. No se creó nada.")

        clave = getpass.getpass("Contraseña (8 a 72 caracteres, no se ve al escribir): ")
        if getpass.getpass("Repite la contraseña: ") != clave:
            sys.exit("Las contraseñas no coinciden.")
        if not 8 <= len(clave) <= 72:
            sys.exit("La contraseña debe tener entre 8 y 72 caracteres.")

        db.add(models.Usuario(nombre_completo=nombre, email=email,
                              password_hash=security.hash_password(clave),
                              rol_id=security.ROL_ADMIN, refugio_id=None))
        db.commit()
        print(f"Administrador creado: {email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
