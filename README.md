# Gestión de solicitudes de crédito

Aplicación full stack para gestionar solicitudes de crédito: crear solicitudes, listarlas con filtro por estado y paginación, y aprobarlas o rechazarlas con un comentario obligatorio. La API REST (FastAPI + PostgreSQL) valida las reglas de negocio y responde todos los errores en formato RFC 9457 (Problem Details); el frontend (Angular) consume la API y muestra esos errores de forma legible.

## Stack

| Capa | Tecnología | Versión |
|---|---|---|
| API | FastAPI + Uvicorn | 0.143.2 / 0.54.0 |
| Datos | SQLAlchemy + Alembic + psycopg 3 | 2.1.4 / 1.20.0 / 3.3.6 |
| Configuración | pydantic-settings | 2.16.0 |
| Base de datos | PostgreSQL (Aurora de Bluecore o Docker local) | 16 |
| Frontend | Angular (standalone, Reactive Forms) | 22.2 |
| Tests | pytest + httpx / Vitest (runner de Angular) | 9.1.1 + 2.13.1 / 5.0 |
| Calidad | Ruff | 0.17.1 |

## Requisitos previos

- Docker Desktop (con `docker compose`)
- Solo para la ejecución manual: Python 3.13 o superior y Node.js 24 con npm

## Ejecutar con Docker

Levanta backend, frontend y (opcionalmente) PostgreSQL con un solo comando. Desde la raíz del repositorio:

```bash
cp .env.example .env        # en PowerShell: Copy-Item .env.example .env
```

Edite `.env` y reemplace `<contraseña>` y `<host-aurora>` por los datos de la base de Bluecore. Luego:

```bash
docker compose up --build
```

| Qué | URL |
|---|---|
| Aplicación | http://localhost:4200 |
| Documentación de la API (Swagger UI) | http://localhost:8000/docs |
| Estado de la API y de la base de datos | http://localhost:8000/health |

Para detener todo: `docker compose down` (añada `-v` para borrar también los datos de la base local). El backend aplica las migraciones (`alembic upgrade head`) en cada arranque.

Para usar la base local en lugar de Aurora, vea [Base de datos](#base-de-datos).

## Puesta en marcha manual

Alternativa sin contenedores para backend y frontend. Todos los comandos parten de la raíz del repositorio. Se necesitan tres terminales (base de datos, backend y frontend); la base de datos puede ser la local en Docker o la Aurora de Bluecore.

### 1. Base de datos

```bash
docker compose --profile local-db up -d db
```

Levanta PostgreSQL 16 en `localhost:5432` y crea automáticamente el rol `usuario_a` y el esquema `esquema_a`. Espere a que el contenedor esté `healthy` (`docker compose ps`). Si usa la Aurora de Bluecore, omita este paso.

### 2. Backend

PowerShell (Windows):

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
Copy-Item .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

Bash (Linux / macOS / Git Bash):

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # en Git Bash de Windows: source .venv/Scripts/activate
pip install -r requirements-dev.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

`backend/.env` debe completarse antes de arrancar: `DATABASE_URL` es obligatoria y no tiene valor por defecto (en `.env.example` está la línea de Aurora activa y la local, con `localhost`, comentada).

Si PowerShell bloquea la activación del entorno virtual, ejecute antes `Set-ExecutionPolicy -Scope Process RemoteSigned`.

### 3. Frontend

```bash
cd frontend
npm install
npx ng serve
```

### 4. URLs

| Qué | URL |
|---|---|
| Aplicación | http://localhost:4200 |
| Documentación interactiva de la API (Swagger UI) | http://localhost:8000/docs |
| Estado de la API y de la base de datos | http://localhost:8000/health |

Con Docker, Nginx reenvía `/api` y `/health` al backend (`frontend/nginx.conf`). En desarrollo, Angular redirige `/api` y `/health` al backend (`frontend/proxy.conf.json`), por lo que los ejemplos `curl` también funcionan contra `http://localhost:4200`.

## Base de datos

- **PostgreSQL y no MySQL:** el host MySQL indicado en el enunciado no resuelve en DNS. Bluecore dispone de un cluster Aurora PostgreSQL 16 (base `demo`) donde al usuario `usuario_a` le corresponde el esquema `esquema_a`, el único en el que puede crear objetos.
- **Solo `esquema_a`:** la aplicación fija `search_path = esquema_a` en la conexión (`DB_SCHEMA`); no lee ni modifica ningún otro esquema. Las tablas y migraciones no llevan el nombre del esquema escrito.
- **Dos bases posibles,** elegidas con `DATABASE_URL` (obligatoria, sin valor por defecto, para no conectarse por error a una base no prevista):

| Opción | Cuándo | `DATABASE_URL` |
|---|---|---|
| Aurora PostgreSQL de Bluecore (por defecto) | Pruebas reales | `postgresql+psycopg://usuario_a:<contraseña>@<host-aurora>:5432/demo?sslmode=require` |
| PostgreSQL local en Docker | Pruebas locales | `postgresql+psycopg://usuario_a:usuario_a@db:5432/demo` (desde contenedores) o `...@localhost:5432/demo` (backend sin Docker) |

- **Cambiar de base:** editar `DATABASE_URL` en `.env` (raíz, para Docker) o en `backend/.env` (backend sin Docker). Para la local con Docker, comente la línea de Aurora, descomente la línea `@db` y ejecute `docker compose --profile local-db up --build`. El servicio `db` solo existe con el perfil `local-db`; sin él, `docker compose up` usa la base indicada en `DATABASE_URL`.
- **Cifrado:** `sslmode=require` cifra con TLS la conexión hacia AWS.
- **Base local:** `docker-compose.yml` reproduce el entorno de Bluecore (PostgreSQL 16, base `demo`, rol `usuario_a` sin privilegios de administrador, esquema `esquema_a`) con el script `docker/postgres/init/01-esquema-a.sql`.
- **Migraciones:** con Docker se aplican solas al arrancar el backend; en ejecución manual, `alembic upgrade head`.

Variables (valores de ejemplo en `.env.example` y `backend/.env.example`): `DATABASE_URL`, `DB_SCHEMA` y, solo en el backend, `CORS_ORIGINS`. Los archivos `.env` están en `.gitignore`; nunca se suben credenciales.

## Tests y calidad

Backend (con el entorno virtual activado, desde `backend/`):

```bash
pytest
ruff check .
ruff format --check .
```

Los tests del backend usan SQLite en memoria: **no requieren Docker ni PostgreSQL**.

Frontend (desde `frontend/`):

```bash
npx ng test --watch=false
npx ng build
```

## API

Base: `http://localhost:8000/api/v1`. Documentación OpenAPI generada en `/docs`.

| Método | Ruta | Descripción | Respuestas |
|---|---|---|---|
| `POST` | `/credit-applications` | Crear solicitud (nace `PENDING`) | `201` + cabecera `Location`; `400`, `422` |
| `GET` | `/credit-applications` | Listar, con filtro `status` y paginación `limit`/`offset` | `200`; `422` |
| `GET` | `/credit-applications/{id}` | Consultar una solicitud | `200`; `404`, `422` |
| `PATCH` | `/credit-applications/{id}/status` | Aprobar o rechazar con comentario | `200`; `400`, `404`, `409`, `422` |
| `GET` | `/health` | Estado de la API y de la base de datos | `200`; `503` |

### Ejemplos

Crear (los ejemplos usan sintaxis bash; en PowerShell use `curl.exe` y comillas simples alrededor del JSON, o la documentación interactiva en `/docs`):

```bash
curl -i -X POST http://localhost:8000/api/v1/credit-applications \
  -H "Content-Type: application/json" \
  -d '{"applicant_document": "8-430-70", "amount": 15000.00, "term_months": 36}'
```

```http
HTTP/1.1 201 Created
location: /api/v1/credit-applications/3f1c7a52-9d0e-4b8e-a6c4-0d2f5b7e9a11
content-type: application/json

{
  "id": "3f1c7a52-9d0e-4b8e-a6c4-0d2f5b7e9a11",
  "applicant_document": "8-430-70",
  "amount": 15000.0,
  "term_months": 36,
  "status": "PENDING",
  "decision_comment": null,
  "decided_at": null,
  "created_at": "2026-10-15T14:32:10Z",
  "updated_at": "2026-10-15T14:32:10Z"
}
```

Listar solicitudes pendientes, segunda página de 10:

```bash
curl "http://localhost:8000/api/v1/credit-applications?status=PENDING&limit=10&offset=10"
```

```json
{ "items": [ { "id": "...", "status": "PENDING", "...": "..." } ], "total": 57, "limit": 10, "offset": 10 }
```

Orden: más recientes primero. `limit` por defecto 20 (1 a 100), `offset` por defecto 0.

Aprobar (use el `id` devuelto al crear):

```bash
curl -X PATCH http://localhost:8000/api/v1/credit-applications/3f1c7a52-9d0e-4b8e-a6c4-0d2f5b7e9a11/status \
  -H "Content-Type: application/json" \
  -d '{"status": "APPROVED", "comment": "Cumple con la política de crédito"}'
```

```json
{
  "id": "3f1c7a52-9d0e-4b8e-a6c4-0d2f5b7e9a11",
  "applicant_document": "8-430-70",
  "amount": 15000.0,
  "term_months": 36,
  "status": "APPROVED",
  "decision_comment": "Cumple con la política de crédito",
  "decided_at": "2026-10-15T14:35:02Z",
  "created_at": "2026-10-15T14:32:10Z",
  "updated_at": "2026-10-15T14:35:02Z"
}
```

Error 422 (datos inválidos):

```bash
curl -i -X POST http://localhost:8000/api/v1/credit-applications \
  -H "Content-Type: application/json" \
  -d '{"applicant_document": "14-1-1", "amount": 100, "term_months": 36}'
```

```http
HTTP/1.1 422 Unprocessable Content
content-type: application/problem+json

{
  "type": "validation_error",
  "title": "Datos inválidos",
  "status": 422,
  "detail": "La solicitud contiene datos inválidos.",
  "errors": [
    { "field": "applicant_document", "message": "La cédula no tiene un formato válido. Ejemplo: 8-430-70." },
    { "field": "amount", "message": "El monto debe estar entre $500.00 y $50,000.00." }
  ]
}
```

Error 409 (repetir la decisión sobre la solicitud ya aprobada):

```bash
curl -i -X PATCH http://localhost:8000/api/v1/credit-applications/3f1c7a52-9d0e-4b8e-a6c4-0d2f5b7e9a11/status \
  -H "Content-Type: application/json" \
  -d '{"status": "REJECTED", "comment": "Segundo intento"}'
```

```http
HTTP/1.1 409 Conflict
content-type: application/problem+json

{
  "type": "application_already_decided",
  "title": "Solicitud ya decidida",
  "status": 409,
  "detail": "La solicitud ya fue aprobada y su decisión es final."
}
```

### Reglas de negocio

| Campo | Regla |
|---|---|
| `amount` | USD, entre 500.00 y 50,000.00 (ambos incluidos), máximo 2 decimales |
| `term_months` | Entero entre 6 y 60 (ambos incluidos) |
| `applicant_document` | Cédula panameña `<prefijo>-<tomo>-<asiento>`, guiones obligatorios. Se normaliza antes de validar (sin espacios, mayúsculas) |
| `comment` (al decidir) | 5 a 500 caracteres tras recortar espacios |
| `status` (al decidir) | Solo `APPROVED` o `REJECTED` (exacto, en mayúsculas) |

Formatos de cédula (tomo: 1 a 4 dígitos; asiento: 1 a 6 dígitos):

| Tipo | Prefijo | Ejemplo |
|---|---|---|
| Panameño | Provincia `1` a `13` | `8-430-70`, `12-1234-12345` |
| Serie antigua (antes de 2006) | Provincia + `AV` | `10AV-1234-12345` |
| Población indígena | Provincia + `PI` | `1PI-1234-12345` |
| Extranjero residente | `E` | `E-8-123456` |
| Naturalizado | `N` | `N-1234-12345` |
| Panameño nacido en el extranjero | `PE` | `PE-5-687` |

Estados: toda solicitud nace `PENDING`; solo una `PENDING` pasa a `APPROVED` o `REJECTED`, y **la decisión es final**. Monto, plazo y cédula no se pueden editar y las solicitudes no se eliminan.

## Formato de errores

Todos los errores (incluidas rutas inexistentes, métodos no permitidos y fallos internos) se responden como Problem Details (RFC 9457), con `Content-Type: application/problem+json` y textos en español. Campos: `type` (código estable para lógica del cliente), `title`, `status`, `detail` (legible, se muestra tal cual) y, solo en validación, `errors[]` con `field` y `message` por campo.

| Status | Cuándo | `type` |
|---|---|---|
| 400 | El cuerpo no es JSON válido | `malformed_request` |
| 404 | La solicitud o la ruta no existe | `not_found` |
| 405 | Método HTTP no permitido en la ruta | `method_not_allowed` |
| 409 | Se decide sobre una solicitud ya decidida | `application_already_decided` |
| 422 | JSON válido que incumple las reglas (monto, plazo, cédula, comentario, estado, `id` mal formado, parámetros de consulta) | `validation_error` |
| 500 | Error inesperado (sin trazas; el detalle va solo al log) | `internal_error` |
| 503 | La base de datos no responde (`/health`) | `service_unavailable` |

## Decisiones de diseño

**API**

- **Recursos en plural y versionados (`/api/v1`):** la acción la indica el método HTTP y la API puede evolucionar sin romper clientes.
- **`PATCH /{id}/status` en lugar de `PUT /{id}`:** no se reemplaza el recurso, solo cambia su estado; deja explícito que monto, plazo y cédula no son editables.
- **Un único endpoint para aprobar y rechazar** (en vez de `/approve` y `/reject`): es la misma operación con distinto valor; evita duplicar lógica.
- **Sin `DELETE`:** en el sector financiero las solicitudes se conservan como registro.
- **Listado paginado** (`limit`/`offset`, con `total`): la tabla crece en un sistema real. Orden por fecha descendente con `id` como desempate para que la paginación sea estable.
- **`201` con cabecera `Location`** al crear.
- **422 y no 400 para validaciones:** el JSON es correcto pero viola las reglas; 400 se reserva para JSON ilegible. **409** para "ya decidida": los datos son válidos pero chocan con el estado actual del recurso.
- **Errores uniformes en Problem Details,** con mensajes de validación de Pydantic traducidos a español y detalle por campo.
- **Textos de cara al usuario en español;** código, tablas y API en inglés.

**Datos y concurrencia**

- **Ids UUID** (texto de 36 caracteres): no revelan cuántas solicitudes existen ni son adivinables.
- **`NUMERIC(10,2)` para el dinero,** nunca `float`: sin errores de redondeo binario. El monto se valida con `Decimal`.
- **Restricciones `CHECK` en la base** (rango de monto, plazo y estados válidos) como defensa en profundidad: la base rechaza datos inválidos aunque alguien escriba sin pasar por la API. Índices sobre `status` y `created_at`, que son los de las consultas del listado.
- **`UPDATE ... WHERE id = :id AND status = 'PENDING'` atómico** para decidir: si dos analistas deciden a la vez, solo uno modifica la fila y el otro recibe `409`. Una solicitud nunca queda aprobada y rechazada a la vez.
- **Fechas en UTC** y expuestas en ISO 8601 con sufijo `Z`.

**Arquitectura**

- **FastAPI:** contrato tipado con Pydantic, OpenAPI automático y ligero para un dominio pequeño. Se descartaron Django + DRF (admin, plantillas y estructura innecesarios aquí) y Flask (validación, documentación y errores habría que armarlos a mano).
- **Capas** `api` → `services` → `repositories` → `models`, más `schemas` (contrato) y `domain` (reglas puras). Las reglas de negocio no conocen HTTP ni la base de datos, así que se prueban sin servidor ni base.
- **Excepciones de dominio** (`ApplicationNotFound`, `ApplicationAlreadyDecided`) traducidas a respuestas en un solo lugar (`core/errors.py`); los endpoints no arman errores a mano.
- **Regla de la cédula en una sola función** con sus tests, y reglas numéricas centralizadas en `domain/rules.py`.

**Frontend**

- **La validación del formulario solo mejora la experiencia;** la que manda es la del backend. Los `errors[]` del 422 se muestran junto a cada campo.
- **Interceptor HTTP centralizado** que convierte cualquier error en un mensaje legible (sin conexión: "No se pudo conectar con el servidor").
- Ante un `409` el diálogo de decisión muestra el mensaje y recarga el listado.
- Reactive Forms, sin librerías de componentes, CSS propio; formato regional `$15,000.00` y fechas `dd/mm/aaaa`.
- Proxy de desarrollo de Angular hacia el backend; el backend además configura CORS (`CORS_ORIGINS`).

## Estructura del proyecto

```
.
├── docker-compose.yml          Backend, frontend y PostgreSQL local (perfil local-db)
├── .env.example                Variables para Docker (copiar a .env)
├── docker/postgres/init/       Crea el rol usuario_a y el esquema esquema_a
├── backend/
│   ├── app/
│   │   ├── main.py             App FastAPI, CORS, routers y handlers de errores
│   │   ├── api/                Endpoints (HTTP <-> servicios)
│   │   ├── schemas/            Contrato Pydantic de entrada y salida
│   │   ├── services/           Reglas de negocio
│   │   ├── domain/             Reglas puras: cédula, estados, límites, excepciones
│   │   ├── repositories/       Acceso a datos
│   │   ├── models/             Modelos ORM
│   │   └── core/               Configuración, sesión de BD, errores
│   ├── alembic/                Migraciones
│   ├── tests/
│   ├── Dockerfile
│   ├── requirements.txt / requirements-dev.txt
│   └── .env.example
├── frontend/
│   ├── Dockerfile              Compilación de Angular + Nginx
│   ├── nginx.conf              Sirve la SPA y reenvía /api y /health al backend
│   ├── proxy.conf.json         Proxy de desarrollo hacia el backend
│   └── src/app/
│       ├── core/               Servicio de API, interceptor de errores, modelos
│       ├── features/credit-applications/   Listado, formulario y diálogo de decisión
│       └── shared/             Etiqueta de estado
└── docs/                       Especificación de diseño
```

## Pendiente / próximos pasos

- Autenticación con JWT (bonus).
