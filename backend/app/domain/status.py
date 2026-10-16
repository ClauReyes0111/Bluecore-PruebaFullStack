from enum import StrEnum


class ApplicationStatus(StrEnum):
    """Estados de una solicitud. Solo PENDING puede pasar a APPROVED o REJECTED."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
