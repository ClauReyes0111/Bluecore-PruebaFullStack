"""Errores de negocio. No saben nada de HTTP: core/errors.py los traduce a respuestas."""

from app.domain.status import ApplicationStatus


class DomainError(Exception):
    pass


class ApplicationNotFound(DomainError):
    def __init__(self, application_id: str) -> None:
        super().__init__(f"Application {application_id} not found")
        self.application_id = application_id


class ApplicationAlreadyDecided(DomainError):
    def __init__(self, application_id: str, current_status: ApplicationStatus) -> None:
        super().__init__(f"Application {application_id} is already {current_status}")
        self.application_id = application_id
        self.current_status = current_status
