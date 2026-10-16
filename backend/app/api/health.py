from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import problem_response
from app.schemas.problem import Problem

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Estado de la API y de la base de datos",
    response_model=dict[str, str],
    responses={
        503: {
            "model": Problem,
            "description": "La base de datos no está disponible.",
            "content": {"application/problem+json": {}},
        }
    },
)
def health(db: Session = Depends(get_db)) -> dict[str, str] | JSONResponse:
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return problem_response(
            503,
            "service_unavailable",
            "Servicio no disponible",
            "La base de datos no está disponible.",
        )
    return {"status": "ok", "database": "ok"}
