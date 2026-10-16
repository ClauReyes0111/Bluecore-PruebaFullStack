# Gestión de solicitudes de crédito — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** API FastAPI + frontend Angular para crear, listar (filtro por estado, paginado) y aprobar/rechazar solicitudes de crédito, con validaciones de negocio, errores RFC 9457 en español, tests y README.

**Architecture:** Backend en capas (`api` → `services` → `repositories` → `models`, con `domain` puro y `core` transversal) sobre MySQL 8 en Docker, esquema versionado con Alembic. Frontend Angular standalone con un servicio de API, un interceptor que normaliza errores y tres piezas de UI (listado, formulario, diálogo de decisión).

**Tech Stack:** Python ≥ 3.13, FastAPI, Pydantic v2, pydantic-settings, SQLAlchemy 2.0, PyMySQL, Alembic, pytest, httpx, Ruff · Angular (estable actual) · MySQL 8.4 (Docker).

**Spec:** `docs/superpowers/specs/2026-10-15-gestion-solicitudes-credito-design.md`

**Alcance:** fases 1–4 de la spec. Las fases 5–6 (Docker completo, JWT) tendrán su propio plan.

## Global Constraints

- Código, tablas, rutas y JSON en inglés (`snake_case` en JSON); todo texto visible para el usuario en español; **comentarios del código en español** solo donde aclaren una decisión.
- Conventional Commits (`feat:`, `fix:`, `test:`, `docs:`, `chore:`, `refactor:`), un cambio lógico por commit, terminando con la línea `Co-Authored-By` indicada por el entorno.
- Prefijo de API `/api/v1`; recurso `credit-applications`; `GET /health` fuera del prefijo.
- Monto USD `500.00`–`50000.00` inclusive, máximo 2 decimales, `Decimal` (nunca `float` en dominio ni BD).
- Plazo entero `6`–`60` inclusive. Comentario de decisión `5`–`500` caracteres tras `strip()`.
- Cédula: normalizar (quitar todos los espacios, mayúsculas) y validar con `^(?:(?:[1-9]|1[0-3])(?:AV|PI)?|E|N|PE)-\d{1,4}-\d{1,6}$`.
- Estados `PENDING` → `APPROVED` | `REJECTED`; la decisión es final (409).
- Todos los errores: `application/problem+json` con `type`, `title`, `status`, `detail` y, solo en validación, `errors: [{field, message}]`.
- Fechas en UTC; se serializan ISO 8601 con sufijo `Z`.
- Ninguna credencial real en el repo; solo `.env.example`.
- Python local disponible: 3.14 (cumple ≥ 3.13). Node: usar **24.19.0** (`nvm use 24.19.0`); el 16 activo no sirve para Angular.

## Review Focus

1. `amount` = `"NaN"`, `"Infinity"` o `1e999` → 422 con mensaje legible, nunca 500 ni registro guardado. (Test en Task 5.)
2. Comentario solo con espacios (`"      "`) → 422 aunque su longitud bruta sea ≥ 5. (Test en Task 5.)
3. `offset` mayor que `total` → `200` con `items: []` y `total` correcto, no 404 ni error. (Test en Task 8.)
4. Monto con céntimos (`1000.10`) → se guarda y devuelve exactamente `1000.1`, sin redondeos binarios. (Test en Task 8.)
5. Doble clic en "Confirmar" del diálogo → una sola petición; el botón se deshabilita mientras se guarda. (Test en Task 12.)

---

## Estructura de archivos

```
.gitignore
docker-compose.yml                      ← solo MySQL (fase 1)
README.md
backend/
  requirements.txt · requirements-dev.txt · pyproject.toml (ruff + pytest) · .env.example · alembic.ini
  alembic/env.py · alembic/versions/0001_create_credit_applications.py
  app/main.py                           ← create_app(), CORS, routers, handlers
  app/core/config.py                    ← Settings
  app/core/database.py                  ← engine, SessionLocal, get_db
  app/core/errors.py                    ← problem_response + handlers
  app/core/clock.py                     ← utc_now()
  app/domain/document.py                ← normalize_document, is_valid_document
  app/domain/status.py                  ← ApplicationStatus
  app/domain/rules.py                   ← constantes de negocio
  app/domain/exceptions.py              ← DomainError y subclases
  app/models/base.py · app/models/credit_application.py
  app/schemas/credit_application.py     ← Create, Read, Page, StatusChange
  app/schemas/problem.py                ← Problem, FieldError (documentación OpenAPI)
  app/repositories/credit_application_repository.py
  app/services/credit_application_service.py
  app/api/credit_applications.py · app/api/health.py
  tests/conftest.py · tests/domain/ · tests/models/ · tests/schemas/ · tests/services/ · tests/repositories/ · tests/api/
frontend/                               ← generado por Angular CLI
  proxy.conf.json
  src/app/app.routes.ts
  src/app/core/models.ts · core/credit-application-api.service.ts · core/error.interceptor.ts · core/notification.service.ts
  src/app/shared/status-badge/
  src/app/features/credit-applications/{application-list,application-form,decision-dialog}/
```

---

## Fase 1 — Base del repositorio

### Task 1: `.gitignore` y MySQL en Docker

**Files:**
- Create: `.gitignore`, `docker-compose.yml`

**Interfaces:**
- Produces: MySQL en `localhost:3306`, base `bluecore`, usuario `bluecore` / contraseña `bluecore` (credenciales solo de desarrollo local).

- [ ] **Step 1: Crear `.gitignore`** con: `.env`, `.venv/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `*.db`, `node_modules/`, `dist/`, `.angular/`, `Prueba_Bluecore*` (evita volver a subir el enunciado con credenciales).

- [ ] **Step 2: Crear `docker-compose.yml`**

```yaml
services:
  db:
    image: mysql:8.4
    environment:
      MYSQL_DATABASE: bluecore
      MYSQL_USER: bluecore
      MYSQL_PASSWORD: bluecore
      MYSQL_ROOT_PASSWORD: rootpassword
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-uroot", "-prootpassword"]
      interval: 5s
      timeout: 5s
      retries: 20

volumes:
  mysql_data:
```

- [ ] **Step 3: Verificar**

Run: `docker compose up -d db` y luego `docker compose ps`
Expected: servicio `db` con estado `healthy` (puede tardar ~30 s).

- [ ] **Step 4: Commit**

```bash
git add .gitignore docker-compose.yml
git commit -m "chore: agregar gitignore y docker-compose con MySQL para desarrollo"
```

---

## Fase 2 — Backend

Todos los comandos de backend se ejecutan desde `backend/` con el entorno virtual activo (`.venv\Scripts\Activate.ps1`).

### Task 2: Esqueleto del backend y `/health`

**Files:**
- Create: `backend/requirements.txt`, `backend/requirements-dev.txt`, `backend/pyproject.toml`, `backend/.env.example`, `backend/app/__init__.py` (y `__init__.py` en cada subpaquete), `backend/app/main.py`, `backend/app/core/config.py`, `backend/app/core/database.py`, `backend/app/core/clock.py`, `backend/app/models/base.py`, `backend/app/api/health.py`
- Test: `backend/tests/conftest.py`, `backend/tests/api/test_health.py`

**Interfaces:**
- Produces:
  - `Settings` con `database_url: str` (default `mysql+pymysql://bluecore:bluecore@localhost:3306/bluecore`) y `cors_origins: list[str]` (default `["http://localhost:4200"]`); `settings = Settings()`; lee `.env`.
  - `engine`, `SessionLocal`, `get_db() -> Iterator[Session]` en `app/core/database.py`.
  - `Base(DeclarativeBase)` en `app/models/base.py`.
  - `utc_now() -> datetime` (naive, UTC, sin microsegundos) en `app/core/clock.py`.
  - `create_app() -> FastAPI` y `app = create_app()` en `app/main.py`.
  - Fixtures `db_session` (SQLite en memoria, `StaticPool`, `Base.metadata.create_all`) y `client` (`TestClient` con `get_db` sobrescrito) en `tests/conftest.py`.

- [ ] **Step 1: Dependencias.** `requirements.txt`: `fastapi`, `uvicorn[standard]`, `sqlalchemy>=2.0`, `pymysql`, `cryptography` (autenticación `caching_sha2_password` de MySQL 8), `alembic`, `pydantic-settings`. `requirements-dev.txt`: `-r requirements.txt`, `pytest`, `httpx`, `ruff`. Crear venv, instalar, y fijar con `==` las versiones instaladas.

- [ ] **Step 2: `pyproject.toml`** con `[tool.ruff]` (`line-length = 100`, `target-version = "py313"`, reglas `E, F, I, UP, B`) y `[tool.pytest.ini_options]` (`testpaths = ["tests"]`, `pythonpath = ["."]`). `.env.example` con `DATABASE_URL=mysql+pymysql://bluecore:bluecore@localhost:3306/bluecore` y `CORS_ORIGINS=["http://localhost:4200"]`.

- [ ] **Step 3: Escribir el test que falla** (`tests/api/test_health.py`)

```python
def test_health_returns_ok_when_database_responds(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}
```

- [ ] **Step 4: Ejecutar y ver que falla.** Run: `pytest tests/api/test_health.py -v` → Expected: FAIL (`ModuleNotFoundError` / 404).

- [ ] **Step 5: Implementar** config, database, clock, base, `create_app()` (título "API de Solicitudes de Crédito", `CORSMiddleware` con `settings.cors_origins`) y `GET /health` que ejecuta `SELECT 1` con la sesión. El caso 503 se agrega en Task 7.

- [ ] **Step 6: Ejecutar.** Run: `pytest -v` y `ruff check . && ruff format --check .` → Expected: PASS y sin hallazgos.

- [ ] **Step 7: Commit** — `chore(backend): crear esqueleto FastAPI con configuración y endpoint de salud`

### Task 3: Validación de cédula panameña (dominio)

**Files:**
- Create: `backend/app/domain/document.py`
- Test: `backend/tests/domain/test_document.py`

**Interfaces:**
- Produces: `normalize_document(raw: str) -> str` (quita todo espacio en blanco, mayúsculas); `is_valid_document(value: str) -> bool` (aplica la regex de Global Constraints sobre un valor **ya normalizado**, con `re.fullmatch`).

- [ ] **Step 1: Escribir los tests que fallan**

```python
VALID = ["8-430-70", "12-1234-12345", "13-1-1", "10AV-1234-12345", "1PI-1234-12345",
         "E-8-123456", "N-1234-12345", "PE-5-687"]
INVALID = ["14-123-456", "0-123-456", "8430700", "8-12345-1", "8-1-1234567", "X-1-1",
           "8AV", "", "8--70", "AV-1-1", "PE-5-687-1", "8-430-70\n"]

@pytest.mark.parametrize("value", VALID)
def test_valid_documents(value): assert is_valid_document(value)

@pytest.mark.parametrize("value", INVALID)
def test_invalid_documents(value): assert not is_valid_document(value)

@pytest.mark.parametrize("raw,expected", [(" pe-5-687 ", "PE-5-687"), ("8 - 430 - 70", "8-430-70"),
                                          ("10av-1-1", "10AV-1-1")])
def test_normalize_document(raw, expected): assert normalize_document(raw) == expected
```

- [ ] **Step 2: Ejecutar y ver que falla.** Run: `pytest tests/domain/test_document.py -v` → FAIL (import).
- [ ] **Step 3: Implementar** ambas funciones; comentario en español explicando por qué los guiones son obligatorios y el rango de provincias 1–13.
- [ ] **Step 4: Ejecutar.** → PASS.
- [ ] **Step 5: Commit** — `feat(backend): validar formato de cédula panameña`

### Task 4: Dominio, modelo ORM y migración

**Files:**
- Create: `backend/app/domain/status.py`, `backend/app/domain/rules.py`, `backend/app/domain/exceptions.py`, `backend/app/models/credit_application.py`, `backend/alembic.ini`, `backend/alembic/env.py`, `backend/alembic/script.py.mako`, `backend/alembic/versions/0001_create_credit_applications.py`
- Test: `backend/tests/models/test_credit_application_constraints.py`

**Interfaces:**
- Produces:
  - `class ApplicationStatus(StrEnum)`: `PENDING`, `APPROVED`, `REJECTED`.
  - `rules.py`: `MIN_AMOUNT = Decimal("500.00")`, `MAX_AMOUNT = Decimal("50000.00")`, `MIN_TERM_MONTHS = 6`, `MAX_TERM_MONTHS = 60`, `MIN_COMMENT_LENGTH = 5`, `MAX_COMMENT_LENGTH = 500`.
  - `exceptions.py`: `DomainError(Exception)`; `ApplicationNotFound(application_id: str)`; `ApplicationAlreadyDecided(application_id: str, current_status: ApplicationStatus)`; ambas guardan sus argumentos como atributos.
  - Modelo `CreditApplication` (`__tablename__ = "credit_applications"`) con las columnas de la spec §5 (`id: Mapped[str]` `String(36)` PK; `amount` `Numeric(10, 2)`; fechas `DateTime` naive UTC), `CheckConstraint`s nombrados `ck_credit_applications_amount_range`, `ck_credit_applications_term_range`, `ck_credit_applications_status_valid`, e índices `ix_credit_applications_status`, `ix_credit_applications_created_at`.

- [ ] **Step 1: Escribir el test que falla** — en SQLite (fixture `db_session`) insertar directamente un `CreditApplication` con `amount=Decimal("499.99")` y otro con `term_months=61` y `status="CANCELLED"`; cada `flush()` debe lanzar `sqlalchemy.exc.IntegrityError`. Un tercero válido (`amount=Decimal("500.00")`, `term_months=6`) hace `flush()` sin error.
- [ ] **Step 2: Ejecutar y ver que falla.** → FAIL (import).
- [ ] **Step 3: Implementar** dominio y modelo. Comentario en español: los `CHECK` son defensa en profundidad además de la validación de la API.
- [ ] **Step 4: Ejecutar.** → PASS.
- [ ] **Step 5: Alembic.** `alembic init alembic`; `env.py` toma la URL de `settings.database_url` y `target_metadata = Base.metadata`. Escribir a mano `0001_create_credit_applications.py` (revision `"0001"`) creando la tabla, los tres `CHECK` y los dos índices; `downgrade` la elimina.
- [ ] **Step 6: Verificar contra MySQL.** Con `docker compose up -d db` y `.env` copiado de `.env.example`: `alembic upgrade head`, luego `docker compose exec db mysql -ubluecore -pbluecore bluecore -e "SHOW CREATE TABLE credit_applications\G"` → Expected: tabla con los 3 `CHECK` y 2 índices. `alembic downgrade base` y `alembic upgrade head` sin errores.
- [ ] **Step 7: Commit** — `feat(backend): agregar modelo de solicitud de crédito y migración inicial`

### Task 5: Esquemas Pydantic con mensajes en español

**Files:**
- Create: `backend/app/schemas/credit_application.py`, `backend/app/schemas/problem.py`
- Test: `backend/tests/schemas/test_credit_application_schemas.py`

**Interfaces:**
- Consumes: `normalize_document`, `is_valid_document` (Task 3); `rules`, `ApplicationStatus` (Task 4).
- Produces:
  - `CreditApplicationCreate(applicant_document: str, amount: Decimal, term_months: int)`, `extra="forbid"`; devuelve la cédula normalizada.
  - `StatusChange(status: str, comment: str)`, `extra="forbid"`; `status` válido solo `"APPROVED"`/`"REJECTED"` (se expone como `ApplicationStatus`); `comment` devuelto con `strip()`.
  - `CreditApplicationRead` (`from_attributes=True`) con los 9 campos de la spec §6.2; `amount` serializado como número JSON (`float`), fechas como ISO 8601 con `Z`.
  - `CreditApplicationPage(items: list[CreditApplicationRead], total: int, limit: int, offset: int)`.
  - `FieldError(field: str, message: str)`, `Problem(type, title, status, detail, errors: list[FieldError] | None = None)`.
  - Las reglas de negocio lanzan `PydanticCustomError(<type>, <mensaje>)` con estos `type` y textos exactos:

| type | mensaje |
|---|---|
| `document_format` | `La cédula no tiene un formato válido. Ejemplo: 8-430-70.` |
| `amount_range` | `El monto debe estar entre $500.00 y $50,000.00.` |
| `amount_decimals` | `El monto admite como máximo 2 decimales.` |
| `term_range` | `El plazo debe estar entre 6 y 60 meses.` |
| `decision_status` | `El estado debe ser APPROVED o REJECTED.` |
| `comment_length` | `El comentario debe tener entre 5 y 500 caracteres.` |

- [ ] **Step 1: Escribir los tests que fallan** — helper `error_types(exc) -> set[str]` sobre `ValidationError.errors()`:
  - monto `499.99`→`amount_range`; `500`, `50000` válidos; `50000.01`→`amount_range`; `100.555`→`amount_decimals`; `"500.000"` válido.
  - **Review Focus 1:** monto `"NaN"`, `"Infinity"` → `ValidationError` (cualquier tipo), sin excepción de otro tipo.
  - plazo `5`, `61`→`term_range`; `6`, `60` válidos; `12.5` → error (no `term_range`).
  - cédula `" pe-5-687 "` → `model.applicant_document == "PE-5-687"`; `"14-1-1"`→`document_format`.
  - campo extra `{"foo": 1}` → `extra_forbidden`.
  - `StatusChange`: `"PENDING"`, `"approved"`, `"CANCELLED"`→`decision_status`; comentario `"abcd"`→`comment_length`; `"a"*501`→`comment_length`; `"  Correcto  "` → `comment == "Correcto"`.
  - **Review Focus 2:** comentario `"      "` → `comment_length`.
  - `CreditApplicationRead` de un objeto con `amount=Decimal("1000.10")` y `created_at=datetime(2026,10,15,21,30)` → `model_dump(mode="json")` da `amount == 1000.1` y `created_at == "2026-10-15T21:30:00Z"`.
- [ ] **Step 2: Ejecutar y ver que falla.** → FAIL.
- [ ] **Step 3: Implementar** con `field_validator(mode="after")`. Decimales: `value != value.quantize(Decimal("0.01"))`. Serializadores con `field_serializer`.
- [ ] **Step 4: Ejecutar.** → PASS.
- [ ] **Step 5: Commit** — `feat(backend): definir esquemas de solicitud con validaciones de negocio`

### Task 6: Repositorio y servicio

**Files:**
- Create: `backend/app/repositories/credit_application_repository.py`, `backend/app/services/credit_application_service.py`
- Test: `backend/tests/repositories/test_credit_application_repository.py`, `backend/tests/services/test_credit_application_service.py`

**Interfaces:**
- Consumes: modelo, `ApplicationStatus`, excepciones (Task 4); esquemas (Task 5); `utc_now` (Task 2).
- Produces:
  - `CreditApplicationRepository(session: Session)`:
    - `add(application: CreditApplication) -> CreditApplication` (commit + refresh)
    - `get(application_id: str) -> CreditApplication | None`
    - `list(status: ApplicationStatus | None, limit: int, offset: int) -> tuple[list[CreditApplication], int]` — orden `created_at DESC, id DESC`; el total respeta el filtro.
    - `decide(application_id: str, status: ApplicationStatus, comment: str, decided_at: datetime) -> bool` — **un solo** `UPDATE ... WHERE id = :id AND status = 'PENDING'` que fija `status`, `decision_comment`, `decided_at`, `updated_at`; commit; devuelve `rowcount == 1`. Comentario en español sobre la concurrencia.
  - `CreditApplicationService(repository, clock: Callable[[], datetime] = utc_now)`:
    - `create(data: CreditApplicationCreate) -> CreditApplication` (id `str(uuid4())`, `PENDING`, `created_at = updated_at = clock()`)
    - `get(application_id: UUID) -> CreditApplication` — lanza `ApplicationNotFound`
    - `list(status, limit, offset) -> tuple[list[CreditApplication], int]`
    - `change_status(application_id: UUID, data: StatusChange) -> CreditApplication` — si `decide` devuelve `False`: `get` → inexistente ⇒ `ApplicationNotFound`; existente ⇒ `ApplicationAlreadyDecided(id, current.status)`.

- [ ] **Step 1: Tests del repositorio que fallan** (SQLite): `test_decide_only_once` (primer `decide` → `True`, segundo con el otro estado → `False`, la fila queda con el primer estado y comentario); `test_list_filters_and_orders` (3 solicitudes con fechas distintas y estados mixtos: filtro `PENDING` devuelve solo pendientes, más reciente primero, `total` correcto, `limit`/`offset` recortan).
- [ ] **Step 2: Tests del servicio que fallan** con un repositorio falso en memoria (sin BD): crear deja `PENDING` y fechas = reloj fijo; `get` inexistente → `ApplicationNotFound`; `change_status` sobre pendiente → estado, comentario y `decided_at` fijados; sobre ya decidida → `ApplicationAlreadyDecided` con `current_status` correcto; sobre inexistente → `ApplicationNotFound`.
- [ ] **Step 3: Ejecutar y ver que fallan.** → FAIL.
- [ ] **Step 4: Implementar.**
- [ ] **Step 5: Ejecutar.** Run: `pytest -v` → PASS.
- [ ] **Step 6: Commit** — `feat(backend): agregar repositorio y servicio de solicitudes con decisión atómica`

### Task 7: Manejo de errores RFC 9457

**Files:**
- Create: `backend/app/core/errors.py`
- Modify: `backend/app/main.py` (registrar handlers), `backend/app/api/health.py` (503)
- Test: `backend/tests/api/test_errors.py`, `backend/tests/api/test_health.py`

**Interfaces:**
- Consumes: excepciones de dominio (Task 4), `FieldError` (Task 5).
- Produces: `problem_response(status: int, type_: str, title: str, detail: str, errors: list[dict] | None = None) -> JSONResponse` (media type `application/problem+json`, omite `errors` si es `None`); `register_exception_handlers(app: FastAPI) -> None`.

Comportamiento (títulos y detalles exactos):

| Origen | status / type | title | detail |
|---|---|---|---|
| `RequestValidationError` con algún error `json_invalid` | 400 `malformed_request` | `Solicitud mal formada` | `El cuerpo de la petición no es un JSON válido.` |
| `RequestValidationError` (resto) | 422 `validation_error` | `Datos inválidos` | `La solicitud contiene datos inválidos.` |
| `ApplicationNotFound` | 404 `not_found` | `Recurso no encontrado` | `No existe una solicitud con id {id}.` |
| HTTP 404 de ruta | 404 `not_found` | `Recurso no encontrado` | `La ruta solicitada no existe.` |
| HTTP 405 | 405 `method_not_allowed` | `Método no permitido` | `El método HTTP no está permitido en esta ruta.` |
| `ApplicationAlreadyDecided` | 409 `application_already_decided` | `Solicitud ya decidida` | `La solicitud ya fue aprobada y su decisión es final.` / `...ya fue rechazada...` |
| `Exception` | 500 `internal_error` | `Error interno` | `Ocurrió un error inesperado. Intente nuevamente más tarde.` (se registra con `logger.exception`) |
| `/health` con `SQLAlchemyError` | 503 `service_unavailable` | `Servicio no disponible` | `La base de datos no está disponible.` |

Traducción de errores de validación a `errors[]`:
- `field`: `".".join(str(p) for p in loc[1:])`, o `loc[0]` si queda vacío; `application_id` se expone como `id`.
- `message`: si el `type` es uno de los propios de Task 5 → `msg` tal cual. Si no, por `type`: `missing` → `Este campo es obligatorio.`; `extra_forbidden` → `Campo no permitido.`; `int_parsing`/`int_type`/`int_from_float` → `Debe ser un número entero.`; `decimal_parsing`/`decimal_type`/`finite_number` → `Debe ser un número válido.`; `string_type` → `Debe ser un texto.`; `uuid_parsing`/`uuid_type` → `El identificador no es un UUID válido.`; `enum` → `Valor no permitido. Valores aceptados: {ctx['expected']}.`; `greater_than_equal` → `Debe ser mayor o igual a {ctx['ge']}.`; `less_than_equal` → `Debe ser menor o igual a {ctx['le']}.`; `model_attributes_type`/`dict_type` → `El cuerpo debe ser un objeto JSON.`; cualquier otro → `Valor inválido.`

- [ ] **Step 1: Tests que fallan:** `GET /no-existe` → 404 `not_found` con `content-type` `application/problem+json`; `DELETE /health` → 405; `/health` con un `get_db` sobrescrito cuya sesión lanza `OperationalError` → 503 `service_unavailable`; una ruta añadida solo en el test que lanza `RuntimeError("secreto")`, con `TestClient(app, raise_server_exceptions=False)` → 500 `internal_error` y el cuerpo **no** contiene `"secreto"`.
- [ ] **Step 2: Ejecutar y ver que fallan.** → FAIL.
- [ ] **Step 3: Implementar** `errors.py`, registrar en `create_app()`, 503 en `/health`.
- [ ] **Step 4: Ejecutar.** → PASS.
- [ ] **Step 5: Commit** — `feat(backend): responder todos los errores con Problem Details en español`

### Task 8: Endpoints de solicitudes

**Files:**
- Create: `backend/app/api/credit_applications.py`
- Modify: `backend/app/main.py` (incluir router)
- Test: `backend/tests/api/test_credit_applications_api.py`

**Interfaces:**
- Consumes: servicio (Task 6), esquemas (Task 5), `get_db` (Task 2), handlers (Task 7).
- Produces (contrato que usa el frontend):
  - `POST /api/v1/credit-applications` → 201, cabecera `Location: /api/v1/credit-applications/{id}`, cuerpo `CreditApplicationRead`.
  - `GET /api/v1/credit-applications?status=&limit=20&offset=0` → 200 `CreditApplicationPage`; `status: ApplicationStatus | None`, `limit` `Query(20, ge=1, le=100)`, `offset` `Query(0, ge=0)`.
  - `GET /api/v1/credit-applications/{application_id}` (`UUID`) → 200.
  - `PATCH /api/v1/credit-applications/{application_id}/status` → 200 `CreditApplicationRead`.
  - Cada ruta declara en `responses=` los códigos de error con modelo `Problem` para que aparezcan en `/docs`.

- [ ] **Step 1: Tests que fallan:**
  - Crear válido → 201, `Location` correcto, `status == "PENDING"`, cédula normalizada.
  - Crear con monto 499.99 y cédula `14-1-1` → 422 `validation_error` con `errors` que contiene `{"field": "amount", "message": "El monto debe estar entre $500.00 y $50,000.00."}` y `{"field": "applicant_document", ...}`.
  - Cuerpo `"{monto: "` (JSON roto, `content-type: application/json`) → 400 `malformed_request`.
  - **Review Focus 4:** crear con `amount: 1000.10` → respuesta `amount == 1000.1`; `GET` por id devuelve lo mismo.
  - Listar con `status=APPROVED` solo trae aprobadas; `status=pending` → 422 con `field == "status"`; `limit=101` → 422.
  - **Review Focus 3:** con 2 solicitudes, `offset=10` → 200, `items == []`, `total == 2`.
  - `GET` id inexistente → 404 `not_found`; id `"abc"` → 422 con `field == "id"`.
  - `PATCH` aprobar pendiente → 200 `APPROVED`, `decision_comment` recortado, `decided_at` no nulo; repetir con `REJECTED` → 409 `application_already_decided` con detail `La solicitud ya fue aprobada y su decisión es final.`; `status: "PENDING"` → 422; id inexistente → 404.
- [ ] **Step 2: Ejecutar y ver que fallan.** → FAIL.
- [ ] **Step 3: Implementar** el router; una dependencia `get_service(db = Depends(get_db)) -> CreditApplicationService`. Los endpoints no construyen errores: solo llaman al servicio.
- [ ] **Step 4: Ejecutar.** Run: `pytest -v && ruff check . && ruff format --check .` → PASS.
- [ ] **Step 5: Prueba manual contra MySQL.** `alembic upgrade head`, `uvicorn app.main:app --reload`; en `http://localhost:8000/docs` crear una solicitud, listarla, aprobarla y volver a aprobarla (409). Expected: mismas respuestas que los tests; la fila existe en MySQL.
- [ ] **Step 6: Commit** — `feat(backend): exponer endpoints REST de solicitudes de crédito`

---

## Fase 3 — Frontend

Todos los comandos desde `frontend/` con Node 24 (`nvm use 24.19.0`; si nvm pide permisos, abrir la terminal como administrador).

### Task 9: Proyecto Angular, modelos, servicio de API e interceptor

**Files:**
- Create: proyecto con `npx @angular/cli@latest new frontend --routing --style=css --ssr=false --skip-git` (desde la raíz); `frontend/proxy.conf.json`; `src/app/core/models.ts`, `src/app/core/credit-application-api.service.ts`, `src/app/core/error.interceptor.ts`, `src/app/core/notification.service.ts`
- Modify: `angular.json` (`serve.options.proxyConfig`), `src/app/app.config.ts` (`provideHttpClient(withInterceptors([errorInterceptor]))`, locale si aplica)
- Test: `src/app/core/error.interceptor.spec.ts`

**Interfaces:**
- Produces (`models.ts`):
  - `type ApplicationStatus = 'PENDING' | 'APPROVED' | 'REJECTED'`
  - `interface CreditApplication` (los 9 campos de la spec §6.2, `amount: number`, fechas `string`)
  - `interface CreditApplicationPage { items; total; limit; offset }`
  - `interface NewCreditApplication { applicant_document: string; amount: number; term_months: number }`
  - `interface StatusChange { status: 'APPROVED' | 'REJECTED'; comment: string }`
  - `interface ApiError { status: number; type: string; title: string; detail: string; fieldErrors: Record<string, string> }`
- `CreditApplicationApiService` (`providedIn: 'root'`): `list(status: ApplicationStatus | null, limit: number, offset: number): Observable<CreditApplicationPage>`, `create(body: NewCreditApplication): Observable<CreditApplication>`, `changeStatus(id: string, body: StatusChange): Observable<CreditApplication>`. URLs relativas `/api/v1/credit-applications`.
- `errorInterceptor: HttpInterceptorFn` — convierte todo `HttpErrorResponse` en `ApiError` (`throwError`): `status 0` → `title: 'Sin conexión'`, `detail: 'No se pudo conectar con el servidor.'`; cuerpo Problem Details → copia `type/title/detail` y convierte `errors[]` a `fieldErrors`; cualquier otro → `title: 'Error'`, `detail: 'Ocurrió un error inesperado.'`.
- `NotificationService`: `message: Signal<string | null>`, `show(text: string)`, `clear()` — mensaje que sobrevive a la navegación.
- `proxy.conf.json`: `/api` y `/health` → `http://localhost:8000`.

- [ ] **Step 1: Generar el proyecto** y verificar que `npx ng test --watch=false` pasa con los tests por defecto. Anotar la versión de Angular generada para el README.
- [ ] **Step 2: Tests que fallan** (`HttpTestingController`): error de red (`status 0`) → `ApiError.detail == 'No se pudo conectar con el servidor.'`; respuesta 422 Problem Details con `errors: [{field:'amount', message:'El monto debe estar entre $500.00 y $50,000.00.'}]` → `fieldErrors.amount` con ese texto y `title == 'Datos inválidos'`.
- [ ] **Step 3: Ejecutar y ver que fallan.** Run: `npx ng test --watch=false` → FAIL.
- [ ] **Step 4: Implementar** modelos, servicio, interceptor, notificaciones, proxy.
- [ ] **Step 5: Ejecutar.** → PASS. `npx ng build` sin errores.
- [ ] **Step 6: Commit** — dos commits: `chore(frontend): crear proyecto Angular con proxy al backend` (solo el scaffold y el proxy) y `feat(frontend): agregar cliente de la API e interceptor de errores`.

### Task 10: Rutas, etiqueta de estado y diseño base

**Files:**
- Create: `src/app/shared/status-badge/status-badge.component.ts` (+ `.css`)
- Modify: `src/app/app.routes.ts`, `src/app/app.component.*` (cabecera "Bluecore · Solicitudes de crédito" y `<router-outlet>`), `src/styles.css`

**Interfaces:**
- Produces: rutas `'' → redirect 'solicitudes'`, `'solicitudes' → ApplicationListComponent`, `'solicitudes/nueva' → ApplicationFormComponent`, `'**' → redirect 'solicitudes'` (componentes cargados con `loadComponent`); `<app-status-badge [status]="...">` que muestra `Pendiente` / `Aprobada` / `Rechazada` con clases `badge--pending|approved|rejected`.

- [ ] **Step 1:** Test de `StatusBadgeComponent`: con `APPROVED` el texto es `Aprobada` y tiene la clase `badge--approved`. Ejecutar → FAIL.
- [ ] **Step 2:** Implementar componente, rutas (componentes vacíos de marcador para lista y formulario) y estilos base (variables de color, tabla, botones, formularios; responsive).
- [ ] **Step 3:** `npx ng test --watch=false` → PASS; `npx ng serve` muestra la cabecera y redirige a `/solicitudes`.
- [ ] **Step 4: Commit** — `feat(frontend): agregar rutas, diseño base y etiqueta de estado`

### Task 11: Formulario de nueva solicitud

**Files:**
- Create/Modify: `src/app/features/credit-applications/application-form/application-form.component.{ts,html,css}`
- Test: `application-form.component.spec.ts`

**Interfaces:**
- Consumes: `CreditApplicationApiService.create`, `ApiError`, `NotificationService` (Task 9).
- Produces: Reactive Form `applicant_document` (requerido, patrón de cédula aplicado sobre el valor normalizado), `amount` (requerido, `min 500`, `max 50000`, máximo 2 decimales), `term_months` (requerido, entero, `min 6`, `max 60`). Mensajes bajo cada campo con los **mismos textos** que el backend (Task 5). Al enviar: botón deshabilitado mientras se guarda; éxito → `notification.show('Solicitud creada correctamente.')` y navegar a `/solicitudes`; `ApiError` con `fieldErrors` → `setErrors({ server: mensaje })` en cada control y se muestra; sin `fieldErrors` → alerta con `detail`. Enlace "Volver al listado".

- [ ] **Step 1: Tests que fallan:** monto `499.99` → control inválido; valores `8-430-70` / `15000` / `24` → formulario válido; tras `create` que emite `ApiError` con `fieldErrors.applicant_document = 'La cédula no tiene un formato válido. Ejemplo: 8-430-70.'` el texto aparece en el DOM.
- [ ] **Step 2:** Ejecutar → FAIL.
- [ ] **Step 3:** Implementar.
- [ ] **Step 4:** Ejecutar → PASS.
- [ ] **Step 5: Commit** — `feat(frontend): agregar formulario de creación de solicitudes`

### Task 12: Listado con filtros, paginación y diálogo de decisión

**Files:**
- Create/Modify: `src/app/features/credit-applications/application-list/application-list.component.{ts,html,css}`, `src/app/features/credit-applications/decision-dialog/decision-dialog.component.{ts,html,css}`
- Test: `decision-dialog.component.spec.ts`

**Interfaces:**
- Consumes: `CreditApplicationApiService.list/changeStatus`, `ApiError`, `NotificationService` (Task 9); `StatusBadgeComponent` (Task 10).
- Produces:
  - `DecisionDialogComponent`: inputs `application: CreditApplication`, `decision: 'APPROVED' | 'REJECTED'`; outputs `decided: CreditApplication`, `conflict: void`, `cancelled: void`. Usa `<dialog>` nativo con `showModal()`. Comentario obligatorio 5–500 caracteres (tras `trim`). Botón "Confirmar aprobación" / "Confirmar rechazo", deshabilitado mientras `saving`. En `ApiError` muestra `detail` dentro del diálogo; si `status === 409` emite además `conflict` y el listado se recarga.
  - `ApplicationListComponent`: filtros Todas / Pendientes / Aprobadas / Rechazadas (señal `status`), página de 20, tabla Fecha (`dd/MM/yyyy`), Cédula, Monto (`currency:'USD'` → `$15,000.00`), Plazo (`24 meses`), Estado (badge), Acciones (Aprobar / Rechazar solo si `PENDING`); paginación "‹ Anterior · 1–20 de 57 · Siguiente ›"; estado vacío "No hay solicitudes para este filtro."; error de carga con `detail` y botón "Reintentar"; muestra y limpia `NotificationService.message`; botón "+ Nueva solicitud".

- [ ] **Step 1: Tests que fallan (diálogo):** comentario `"abcd"` → botón deshabilitado; **Review Focus 5:** con comentario válido, dos clics seguidos en "Confirmar" → `changeStatus` llamado **una vez** (espía que devuelve un `Subject` sin completar) y el botón queda deshabilitado; con `ApiError` 409 se muestra `La solicitud ya fue aprobada y su decisión es final.`
- [ ] **Step 2:** Ejecutar → FAIL.
- [ ] **Step 3:** Implementar diálogo y listado.
- [ ] **Step 4:** `npx ng test --watch=false` → PASS; `npx ng build` sin errores.
- [ ] **Step 5: Prueba manual de punta a punta** con backend + MySQL corriendo: crear 3 solicitudes, filtrar por cada estado, aprobar una, rechazar otra, intentar decidir una ya decidida desde otra pestaña (409 visible), enviar monto 499 desde el formulario y ver el mensaje, detener el backend y ver "No se pudo conectar con el servidor."
- [ ] **Step 6: Commit** — dos commits: `feat(frontend): agregar diálogo de aprobación y rechazo` y `feat(frontend): agregar listado de solicitudes con filtros y paginación`.

---

## Fase 4 — README y verificación final

### Task 13: README y prueba desde cero

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Escribir el README** en español: descripción; stack con versiones reales; requisitos (Docker Desktop, Python ≥ 3.13, Node 24); pasos numerados (1. `docker compose up -d db`; 2. backend: venv, `pip install -r requirements-dev.txt`, copiar `.env.example` a `.env`, `alembic upgrade head`, `uvicorn app.main:app --reload`; 3. frontend: `npm install`, `npx ng serve`, abrir `http://localhost:4200`); cómo correr tests y linter de ambos lados; tabla de endpoints con ejemplos `curl` (crear, listar filtrado, aprobar, error 422 y 409); formato de errores; sección **"Decisiones de diseño"** con las justificaciones de la spec §4–§8; nota sobre el host MySQL del enunciado que no resuelve y cómo apuntar a otro servidor cambiando `DATABASE_URL`; estructura de carpetas.
- [ ] **Step 2: Verificación desde cero:** clonar el repo en una carpeta temporal, `docker compose down -v` en el original, y seguir el README **literalmente** sin pasos extra. Expected: tests de backend y frontend en verde, app funcionando en `http://localhost:4200`. Corregir el README ante cualquier paso faltante.
- [ ] **Step 3: Commit** — `docs: documentar instalación, uso, API y decisiones de diseño`
