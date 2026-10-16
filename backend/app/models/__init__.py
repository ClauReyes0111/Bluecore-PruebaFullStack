# Importar los modelos aquí registra sus tablas en Base.metadata (lo usan Alembic y los tests)
from app.models.base import Base
from app.models.credit_application import CreditApplication

__all__ = ["Base", "CreditApplication"]
