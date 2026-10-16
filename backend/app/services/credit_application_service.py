from collections.abc import Callable
from datetime import datetime
from uuid import UUID, uuid4

from app.core.clock import utc_now
from app.domain.exceptions import ApplicationAlreadyDecided, ApplicationNotFound
from app.domain.status import ApplicationStatus
from app.models.credit_application import CreditApplication
from app.repositories.credit_application_repository import CreditApplicationRepository
from app.schemas.credit_application import CreditApplicationCreate, StatusChange


class CreditApplicationService:
    def __init__(
        self,
        repository: CreditApplicationRepository,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self._repository = repository
        self._clock = clock

    def create(self, data: CreditApplicationCreate) -> CreditApplication:
        now = self._clock()
        application = CreditApplication(
            id=str(uuid4()),
            applicant_document=data.applicant_document,
            amount=data.amount,
            term_months=data.term_months,
            status=ApplicationStatus.PENDING,
            created_at=now,
            updated_at=now,
        )
        return self._repository.add(application)

    def get(self, application_id: UUID) -> CreditApplication:
        application = self._repository.get(str(application_id))
        if application is None:
            raise ApplicationNotFound(str(application_id))
        return application

    def list(
        self, status: ApplicationStatus | None, limit: int, offset: int
    ) -> tuple[list[CreditApplication], int]:
        return self._repository.list(status, limit, offset)

    def change_status(self, application_id: UUID, data: StatusChange) -> CreditApplication:
        key = str(application_id)
        decided = self._repository.decide(key, data.status, data.comment, self._clock())
        # get() lanza ApplicationNotFound si no existe; si existe y no se pudo decidir,
        # es porque ya no estaba PENDING
        current = self.get(application_id)
        if not decided:
            raise ApplicationAlreadyDecided(key, ApplicationStatus(current.status))
        return current
