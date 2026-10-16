from pydantic import BaseModel


class FieldError(BaseModel):
    field: str
    message: str


class Problem(BaseModel):
    """Formato único de error de la API (se usa para documentar las respuestas en OpenAPI)."""

    type: str
    title: str
    status: int
    detail: str
    errors: list[FieldError] | None = None
