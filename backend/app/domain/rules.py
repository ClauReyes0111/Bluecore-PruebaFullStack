"""Reglas de negocio de la solicitud de crédito, en un solo lugar."""

from decimal import Decimal

# Monto en USD (moneda de uso en Panamá), ambos extremos incluidos
MIN_AMOUNT = Decimal("500.00")
MAX_AMOUNT = Decimal("50000.00")

# Plazo en meses, ambos extremos incluidos
MIN_TERM_MONTHS = 6
MAX_TERM_MONTHS = 60

# Comentario obligatorio al aprobar o rechazar
MIN_COMMENT_LENGTH = 5
MAX_COMMENT_LENGTH = 500
