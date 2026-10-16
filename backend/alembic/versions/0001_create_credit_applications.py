"""Crear la tabla credit_applications.

Revision ID: 0001
Revises:
Create Date: 2026-10-15
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "credit_applications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("applicant_document", sa.String(20), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("term_months", sa.SmallInteger(), nullable=False),
        sa.Column("status", sa.String(10), nullable=False, server_default="PENDING"),
        sa.Column("decision_comment", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        # Defensa en profundidad: mismos límites que app/domain/rules.py
        sa.CheckConstraint(
            "amount >= 500 AND amount <= 50000", name="ck_credit_applications_amount_range"
        ),
        sa.CheckConstraint(
            "term_months >= 6 AND term_months <= 60", name="ck_credit_applications_term_range"
        ),
        sa.CheckConstraint(
            "status IN ('PENDING', 'APPROVED', 'REJECTED')",
            name="ck_credit_applications_status_valid",
        ),
    )
    op.create_index("ix_credit_applications_status", "credit_applications", ["status"])
    op.create_index("ix_credit_applications_created_at", "credit_applications", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_credit_applications_created_at", table_name="credit_applications")
    op.drop_index("ix_credit_applications_status", table_name="credit_applications")
    op.drop_table("credit_applications")
