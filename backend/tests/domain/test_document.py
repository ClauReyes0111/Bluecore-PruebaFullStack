import pytest

from app.domain.document import is_valid_document, normalize_document

VALID = [
    "8-430-70",  # panameño, cédula corta
    "12-1234-12345",  # panameño, cédula larga
    "13-1-1",  # provincia 13 (Panamá Oeste)
    "10AV-1234-12345",  # serie antigua
    "1PI-1234-12345",  # población indígena
    "E-8-123456",  # extranjero residente
    "N-1234-12345",  # naturalizado
    "PE-5-687",  # panameño nacido en el extranjero
]

INVALID = [
    "14-123-456",  # provincia inexistente
    "0-123-456",  # provincia 0
    "8430700",  # sin guiones: ambiguo
    "8-12345-1",  # tomo de 5 dígitos
    "8-1-1234567",  # asiento de 7 dígitos
    "X-1-1",  # prefijo desconocido
    "8AV",  # incompleta
    "",
    "8--70",  # tomo vacío
    "AV-1-1",  # AV sin provincia
    "PE-5-687-1",  # segmento extra
    "8-430-70\n",  # salto de línea al final
    "8-٤٣٠-70",  # dígitos arábigo-índicos: solo se aceptan 0-9
]


@pytest.mark.parametrize("value", VALID)
def test_valid_documents(value):
    assert is_valid_document(value)


@pytest.mark.parametrize("value", INVALID)
def test_invalid_documents(value):
    assert not is_valid_document(value)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [(" pe-5-687 ", "PE-5-687"), ("8 - 430 - 70", "8-430-70"), ("10av-1-1", "10AV-1-1")],
)
def test_normalize_document(raw, expected):
    assert normalize_document(raw) == expected
