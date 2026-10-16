import uuid
from datetime import UTC, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_serializer, field_validator
from pydantic_core import PydanticCustomError

from app.domain import rules
from app.domain.document import is_valid_document, normalize_document
from app.domain.status import ApplicationStatus

_CENTS = Decimal("0.01")
_DECISION_STATUSES = (ApplicationStatus.APPROVED, ApplicationStatus.REJECTED)


def _to_utc_iso(value: datetime | None) -> str | None:
    """Las fechas se guardan en UTC sin zona horaria; se exponen con sufijo Z."""
    if value is None:
        return None
    if value.tzinfo is not None:
        value = value.astimezone(UTC).replace(tzinfo=None)
    return value.isoformat() + "Z"


class CreditApplicationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    applicant_document: str
    amount: Decimal
    term_months: int

    @field_validator("applicant_document", mode="after")
    @classmethod
    def validate_document(cls, value: str) -> str:
        normalized = normalize_document(value)
        if not is_valid_document(normalized):
            raise PydanticCustomError(
                "document_format", "La cédula no tiene un formato válido. Ejemplo: 8-430-70."
            )
        return normalized

    @field_validator("amount", mode="after")
    @classmethod
    def validate_amount(cls, value: Decimal) -> Decimal:
        # Los decimales se revisan primero: 100.555 también está fuera de rango y debe
        # reportar el error de decimales (así lo exige el test)
        # Pydantic ya rechaza NaN e Infinity para Decimal, por lo que aquí el valor es finito
        if value != value.quantize(_CENTS):
            raise PydanticCustomError("amount_decimals", "El monto admite como máximo 2 decimales.")
        if not rules.MIN_AMOUNT <= value <= rules.MAX_AMOUNT:
            raise PydanticCustomError(
                "amount_range", "El monto debe estar entre $500.00 y $50,000.00."
            )
        return value

    @field_validator("term_months", mode="after")
    @classmethod
    def validate_term(cls, value: int) -> int:
        if not rules.MIN_TERM_MONTHS <= value <= rules.MAX_TERM_MONTHS:
            raise PydanticCustomError("term_range", "El plazo debe estar entre 6 y 60 meses.")
        return value


class StatusChange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Se declara str (no el enum) para que "PENDING" falle con nuestro mensaje en español
    status: str
    comment: str

    @field_validator("status", mode="after")
    @classmethod
    def validate_status(cls, value: str) -> ApplicationStatus:
        # Coincidencia exacta y sensible a mayúsculas: "approved" no es válido
        if value not in _DECISION_STATUSES:
            raise PydanticCustomError("decision_status", "El estado debe ser APPROVED o REJECTED.")
        return ApplicationStatus(value)

    @field_validator("comment", mode="after")
    @classmethod
    def validate_comment(cls, value: str) -> str:
        # Se recorta antes de medir para que un comentario de solo espacios sea inválido
        trimmed = value.strip()
        if not rules.MIN_COMMENT_LENGTH <= len(trimmed) <= rules.MAX_COMMENT_LENGTH:
            raise PydanticCustomError(
                "comment_length", "El comentario debe tener entre 5 y 500 caracteres."
            )
        return trimmed


class CreditApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    applicant_document: str
    amount: Decimal
    term_months: int
    status: ApplicationStatus
    decision_comment: str | None
    decided_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @field_serializer("amount", when_used="json")
    def serialize_amount(self, value: Decimal) -> float:
        return float(value)

    @field_serializer("decided_at", "created_at", "updated_at", when_used="json")
    def serialize_datetime(self, value: datetime | None) -> str | None:
        return _to_utc_iso(value)


class CreditApplicationPage(BaseModel):
    items: list[CreditApplicationRead]
    total: int
    limit: int
    offset: int
