from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.domain.status import ApplicationStatus
from app.models.credit_application import CreditApplication


class CreditApplicationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, application: CreditApplication) -> CreditApplication:
        self._session.add(application)
        self._session.commit()
        self._session.refresh(application)
        return application

    def get(self, application_id: str) -> CreditApplication | None:
        return self._session.get(CreditApplication, application_id)

    def list(
        self, status: ApplicationStatus | None, limit: int, offset: int
    ) -> tuple[list[CreditApplication], int]:
        query = select(CreditApplication)
        count_query = select(func.count()).select_from(CreditApplication)
        if status is not None:
            query = query.where(CreditApplication.status == status)
            count_query = count_query.where(CreditApplication.status == status)
        # id como desempate para que la paginación sea estable con fechas iguales
        query = (
            query.order_by(CreditApplication.created_at.desc(), CreditApplication.id.desc())
            .limit(limit)
            .offset(offset)
        )
        items = list(self._session.scalars(query))
        total = self._session.scalar(count_query)
        return items, total

    def decide(
        self, application_id: str, status: ApplicationStatus, comment: str, decided_at: datetime
    ) -> bool:
        # Un único UPDATE condicional (status = 'PENDING') es atómico en la base: si dos
        # analistas deciden a la vez, solo uno modifica la fila y el otro recibe rowcount 0.
        # "fetch" refresca el objeto ya cargado en la sesión (expire_on_commit=False).
        result = self._session.execute(
            update(CreditApplication)
            .where(
                CreditApplication.id == application_id,
                CreditApplication.status == ApplicationStatus.PENDING,
            )
            .values(
                status=status,
                decision_comment=comment,
                decided_at=decided_at,
                updated_at=decided_at,
            )
            .execution_options(synchronize_session="fetch")
        )
        self._session.commit()
        return result.rowcount == 1
