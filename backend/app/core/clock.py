from datetime import UTC, datetime


def utc_now() -> datetime:
    """Hora actual en UTC, sin zona horaria ni microsegundos.

    La columna TIMESTAMP de PostgreSQL (sin zona horaria) no guarda zona: se guarda todo
    en UTC por convención y se descartan los microsegundos para que lo guardado y lo
    devuelto sean idénticos.
    """
    return datetime.now(UTC).replace(tzinfo=None, microsecond=0)
