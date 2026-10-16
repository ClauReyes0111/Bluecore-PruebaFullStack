from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health
from app.core.config import settings
from app.core.errors import register_exception_handlers


def create_app() -> FastAPI:
    app = FastAPI(
        title="API de Solicitudes de Crédito",
        description="Gestión de solicitudes de crédito: creación, listado y decisión.",
        version="1.0.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["Content-Type"],
        expose_headers=["Location"],
    )
    register_exception_handlers(app)
    app.include_router(health.router)
    return app


app = create_app()
