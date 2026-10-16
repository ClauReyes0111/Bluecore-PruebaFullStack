from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domain.status import ApplicationStatus
from app.repositories.credit_application_repository import CreditApplicationRepository
from app.schemas.credit_application import (
    CreditApplicationCreate,
    CreditApplicationPage,
    CreditApplicationRead,
    StatusChange,
)
from app.schemas.problem import Problem
from app.services.credit_application_service import CreditApplicationService

router = APIRouter(prefix="/api/v1/credit-applications", tags=["credit-applications"])


def _problem(description: str) -> dict:
    return {
        "model": Problem,
        "description": description,
        "content": {"application/problem+json": {}},
    }


_VALIDATION = _problem("Datos inválidos.")
_NOT_FOUND = _problem("La solicitud no existe.")


def get_service(db: Session = Depends(get_db)) -> CreditApplicationService:
    return CreditApplicationService(CreditApplicationRepository(db))


@router.post(
    "",
    status_code=201,
    summary="Crear una solicitud de crédito",
    response_model=CreditApplicationRead,
    responses={400: _problem("El cuerpo no es un JSON válido."), 422: _VALIDATION},
)
def create_application(
    data: CreditApplicationCreate,
    response: Response,
    service: CreditApplicationService = Depends(get_service),
) -> CreditApplicationRead:
    application = service.create(data)
    response.headers["Location"] = f"{router.prefix}/{application.id}"
    return CreditApplicationRead.model_validate(application)


@router.get(
    "",
    summary="Listar solicitudes de crédito",
    response_model=CreditApplicationPage,
    responses={422: _VALIDATION},
)
def list_applications(
    status: ApplicationStatus | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: CreditApplicationService = Depends(get_service),
) -> CreditApplicationPage:
    items, total = service.list(status, limit, offset)
    return CreditApplicationPage(
        items=[CreditApplicationRead.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{application_id}",
    summary="Consultar una solicitud de crédito",
    response_model=CreditApplicationRead,
    responses={404: _NOT_FOUND, 422: _VALIDATION},
)
def get_application(
    application_id: UUID, service: CreditApplicationService = Depends(get_service)
) -> CreditApplicationRead:
    return CreditApplicationRead.model_validate(service.get(application_id))


@router.patch(
    "/{application_id}/status",
    summary="Aprobar o rechazar una solicitud de crédito",
    response_model=CreditApplicationRead,
    responses={
        400: _problem("El cuerpo no es un JSON válido."),
        404: _NOT_FOUND,
        409: _problem("La solicitud ya fue decidida y la decisión es final."),
        422: _VALIDATION,
    },
)
def change_status(
    application_id: UUID,
    data: StatusChange,
    service: CreditApplicationService = Depends(get_service),
) -> CreditApplicationRead:
    return CreditApplicationRead.model_validate(service.change_status(application_id, data))
