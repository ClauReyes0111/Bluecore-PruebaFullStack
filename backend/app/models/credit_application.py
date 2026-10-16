from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Index, Numeric, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.status import ApplicationStatus
from app.models.base import Base


class CreditApplication(Base):
    __tablename__ = "credit_applications"
    # Defensa en profundidad: la base rechaza datos inválidos aunque alguien escriba
    # sin pasar por la API. Los mismos límites están en app/domain/rules.py.
    __table_args__ = (
        CheckConstraint(
            "amount >= 500 AND amount <= 50000", name="ck_credit_applications_amount_range"
        ),
        CheckConstraint(
            "term_months >= 6 AND term_months <= 60", name="ck_credit_applications_term_range"
        ),
        CheckConstraint(
            "status IN ('PENDING', 'APPROVED', 'REJECTED')",
            name="ck_credit_applications_status_valid",
        ),
        Index("ix_credit_applications_status", "status"),
        Index("ix_credit_applications_created_at", "created_at"),
    )

    # UUID como texto: no expone cuántas solicitudes hay ni permite adivinar ids
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    applicant_document: Mapped[str] = mapped_column(String(20))
    # DECIMAL y no float: el dinero no admite errores de redondeo binario
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    term_months: Mapped[int] = mapped_column(SmallInteger)
    status: Mapped[str] = mapped_column(String(10), default=ApplicationStatus.PENDING)
    decision_comment: Mapped[str | None] = mapped_column(Text)
    # Todas las fechas en UTC
    decided_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)
