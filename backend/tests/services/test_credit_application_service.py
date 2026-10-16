from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain.exceptions import ApplicationAlreadyDecided, ApplicationNotFound
from app.domain.status import ApplicationStatus
from app.models.credit_application import CreditApplication
from app.schemas.credit_application import CreditApplicationCreate, StatusChange
from app.services.credit_application_service import CreditApplicationService

NOW = datetime(2026, 10, 15, 12, 0, 0)


class FakeRepository:
    def __init__(self) -> None:
        self.items: dict[str, CreditApplication] = {}

    def add(self, application):
        self.items[application.id] = application
        return application

    def get(self, application_id):
        return self.items.get(application_id)

    def list(self, status, limit, offset):
        rows = [a for a in self.items.values() if status is None or a.status == status]
        return rows[offset : offset + limit], len(rows)

    def decide(self, application_id, status, comment, decided_at):
        application = self.items.get(application_id)
        if application is None or application.status != ApplicationStatus.PENDING:
            return False
        application.status = status
        application.decision_comment = comment
        application.decided_at = decided_at
        application.updated_at = decided_at
        return True


@pytest.fixture
def service() -> CreditApplicationService:
    return CreditApplicationService(FakeRepository(), clock=lambda: NOW)


def new_application(service: CreditApplicationService) -> CreditApplication:
    data = CreditApplicationCreate(
        applicant_document="8-430-70", amount=Decimal("1000.10"), term_months=12
    )
    return service.create(data)


def test_create_sets_pending_and_clock_dates(service):
    created = new_application(service)

    assert created.status == ApplicationStatus.PENDING
    assert created.created_at == NOW
    assert created.updated_at == NOW
    assert created.amount == Decimal("1000.10")
    assert len(created.id) == 36


def test_get_unknown_raises_not_found(service):
    with pytest.raises(ApplicationNotFound):
        service.get(uuid4())


def test_get_returns_created(service):
    created = new_application(service)

    assert service.get(created.id).id == created.id


def test_list_delegates_to_repository(service):
    new_application(service)

    items, total = service.list(ApplicationStatus.PENDING, limit=10, offset=0)

    assert len(items) == 1
    assert total == 1


def test_change_status_on_pending(service):
    created = new_application(service)

    result = service.change_status(
        created.id, StatusChange(status="APPROVED", comment="Cumple requisitos")
    )

    assert result.status == ApplicationStatus.APPROVED
    assert result.decision_comment == "Cumple requisitos"
    assert result.decided_at == NOW


def test_change_status_on_decided_raises_conflict(service):
    created = new_application(service)
    service.change_status(created.id, StatusChange(status="REJECTED", comment="Sin capacidad"))

    with pytest.raises(ApplicationAlreadyDecided) as error:
        service.change_status(created.id, StatusChange(status="APPROVED", comment="Reconsiderada"))

    assert error.value.current_status == ApplicationStatus.REJECTED


def test_change_status_on_unknown_raises_not_found(service):
    with pytest.raises(ApplicationNotFound):
        service.change_status(uuid4(), StatusChange(status="APPROVED", comment="Comentario"))
