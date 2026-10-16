"""Todos los errores de la API salen como Problem Details (RFC 9457) con textos en español."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.domain.exceptions import ApplicationAlreadyDecided, ApplicationNotFound
from app.domain.status import ApplicationStatus

logger = logging.getLogger(__name__)

# Errores propios de schemas/credit_application.py: su mensaje ya está en español
_CUSTOM_ERROR_TYPES = {
    "document_format",
    "amount_range",
    "amount_decimals",
    "term_range",
    "decision_status",
    "comment_length",
}

_MESSAGES = {
    "missing": "Este campo es obligatorio.",
    "extra_forbidden": "Campo no permitido.",
    "int_parsing": "Debe ser un número entero.",
    "int_type": "Debe ser un número entero.",
    "int_from_float": "Debe ser un número entero.",
    "decimal_parsing": "Debe ser un número válido.",
    "decimal_type": "Debe ser un número válido.",
    "finite_number": "Debe ser un número válido.",
    "string_type": "Debe ser un texto.",
    "uuid_parsing": "El identificador no es un UUID válido.",
    "uuid_type": "El identificador no es un UUID válido.",
    "model_attributes_type": "El cuerpo debe ser un objeto JSON.",
    "dict_type": "El cuerpo debe ser un objeto JSON.",
}


def problem_response(
    status: int, type_: str, title: str, detail: str, errors: list[dict] | None = None
) -> JSONResponse:
    content: dict = {"type": type_, "title": title, "status": status, "detail": detail}
    if errors is not None:
        content["errors"] = errors
    return JSONResponse(content, status_code=status, media_type="application/problem+json")


def _field_name(loc: tuple) -> str:
    name = ".".join(str(part) for part in loc[1:]) or str(loc[0])
    return "id" if name == "application_id" else name


def _message(error: dict) -> str:
    error_type = error["type"]
    ctx = error.get("ctx", {})
    if error_type in _CUSTOM_ERROR_TYPES:
        return error["msg"]
    if error_type == "enum":
        # Pydantic arma la lista en inglés ("'A', 'B' or 'C'")
        expected = ctx["expected"].replace(" or ", " o ")
        return f"Valor no permitido. Valores aceptados: {expected}."
    if error_type == "greater_than_equal":
        return f"Debe ser mayor o igual a {ctx['ge']}."
    if error_type == "less_than_equal":
        return f"Debe ser menor o igual a {ctx['le']}."
    return _MESSAGES.get(error_type, "Valor inválido.")


async def _validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # JSON ilegible es un fallo de sintaxis (400); JSON válido con datos incorrectos es 422
    if any(error["type"] == "json_invalid" for error in exc.errors()):
        return problem_response(
            400,
            "malformed_request",
            "Solicitud mal formada",
            "El cuerpo de la petición no es un JSON válido.",
        )
    errors = [{"field": _field_name(e["loc"]), "message": _message(e)} for e in exc.errors()]
    return problem_response(
        422, "validation_error", "Datos inválidos", "La solicitud contiene datos inválidos.", errors
    )


async def _http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    if exc.status_code == 404:
        return problem_response(
            404, "not_found", "Recurso no encontrado", "La ruta solicitada no existe."
        )
    if exc.status_code == 405:
        return problem_response(
            405,
            "method_not_allowed",
            "Método no permitido",
            "El método HTTP no está permitido en esta ruta.",
        )
    return problem_response(exc.status_code, "http_error", "Error en la solicitud", str(exc.detail))


async def _not_found_handler(request: Request, exc: ApplicationNotFound) -> JSONResponse:
    return problem_response(
        404,
        "not_found",
        "Recurso no encontrado",
        f"No existe una solicitud con id {exc.application_id}.",
    )


async def _already_decided_handler(
    request: Request, exc: ApplicationAlreadyDecided
) -> JSONResponse:
    word = "aprobada" if exc.current_status == ApplicationStatus.APPROVED else "rechazada"
    return problem_response(
        409,
        "application_already_decided",
        "Solicitud ya decidida",
        f"La solicitud ya fue {word} y su decisión es final.",
    )


async def _unexpected_handler(request: Request, exc: Exception) -> JSONResponse:
    # El detalle real solo va al log: la respuesta nunca debe filtrar información interna
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return problem_response(
        500,
        "internal_error",
        "Error interno",
        "Ocurrió un error inesperado. Intente nuevamente más tarde.",
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, _validation_handler)
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)
    app.add_exception_handler(ApplicationNotFound, _not_found_handler)
    app.add_exception_handler(ApplicationAlreadyDecided, _already_decided_handler)
    app.add_exception_handler(Exception, _unexpected_handler)
