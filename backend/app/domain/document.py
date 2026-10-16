"""Validación de la cédula panameña: <prefijo>-<tomo>-<asiento>."""

import re

# Prefijo:
#   - provincia 1–13 (10 provincias + 3 comarcas; 13 = Panamá Oeste), sola o seguida de
#     AV (serie antigua, antes de 2006) o PI (población indígena);
#   - E (extranjero residente), N (naturalizado), PE (panameño nacido en el extranjero).
# Tomo: 1–4 dígitos. Asiento: 1–6 dígitos.
# Los guiones son obligatorios: sin ellos "8430700" sería ambiguo (8-430-700 u 84-30-700).
# Se usa [0-9] y no \d porque en Python \d también acepta dígitos de otros alfabetos.
_DOCUMENT_PATTERN = re.compile(r"(?:(?:[1-9]|1[0-3])(?:AV|PI)?|E|N|PE)-[0-9]{1,4}-[0-9]{1,6}")

_WHITESPACE = re.compile(r"\s+")


def normalize_document(raw: str) -> str:
    """Quita todos los espacios y pasa a mayúsculas: ' pe-5-687 ' -> 'PE-5-687'."""
    return _WHITESPACE.sub("", raw).upper()


def is_valid_document(value: str) -> bool:
    """Valida una cédula ya normalizada."""
    # fullmatch (y no match con ^...$) para no aceptar un salto de línea al final
    return _DOCUMENT_PATTERN.fullmatch(value) is not None
