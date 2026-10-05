from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Reemplaza 'tu_contraseña_aqui' con tu clave real
SQLALCHEMY_DATABASE_URL = "postgresql://usuario_adopcion:Usudop.2026!@localhost:5432/adopcion_ecommerce"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()