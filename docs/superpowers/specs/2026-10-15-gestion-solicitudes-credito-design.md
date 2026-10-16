# Gestión de solicitudes de crédito — Diseño

- **Fecha:** 2026-10-15
- **Contexto:** Prueba técnica Full Stack de Bluecore (sector financiero, Panamá y Latam)
- **Estado:** Aprobado sección por sección en conversación; pendiente de revisión del documento completo

## 1. Objetivo

Construir una aplicación para gestionar solicitudes de crédito con un flujo completo:
crear solicitudes, listarlas filtrando por estado y aprobarlas o rechazarlas con un comentario.

El diseño busca ser **realista para el sector financiero** y fácil de justificar en la entrevista
de seguimiento.

### Criterios de éxito

- El proyecto corre sin modificaciones siguiendo el README.
- Cubre los criterios base de la prueba: diseño de API (25), validaciones (15), errores HTTP (10),
  frontend conectado (15), calidad de código (15), README (10), tests (10).
- Los errores llegan legibles al frontend, no solo como código HTTP.
- Historial de Git con commits atómicos y descriptivos.
- Cada decisión de diseño tiene una justificación explícita (secciones 4 a 8).

### Fuera de alcance (por ahora)

- Dockerizar backend y frontend, y autenticación JWT: son bonus y se hacen **al final**,
  una vez que la base esté completa y verificada (sección 9).
- Edición o eliminación de solicitudes, historial de múltiples cambios de estado.

## 2. Stack

| Capa | Tecnología | Motivo |
|---|---|---|
| Backend | Python 3.13 + FastAPI | Contrato de API declarado y tipado (Pydantic), documentación OpenAPI automática, ligero para un dominio pequeño |
| ORM y migraciones | SQLAlchemy 2.0 + Alembic | Esquema versionado como en producción |
| Base de datos | PostgreSQL 16, esquema `esquema_a` (Aurora de Bluecore; PostgreSQL 16 en Docker para desarrollo) | El entorno asignado al candidato (ver 2.1) |
| Frontend | Angular (versión estable actual, standalone components) | Bonus de la prueba; se adopta desde el inicio para no hacer trabajo doble |
| Tests | pytest (backend), runner por defecto de Angular (frontend) | |
| Estilo | Ruff (backend) | |

**Alternativas descartadas para el backend:** Django + DRF (trae admin, plantillas y estructura que
esta prueba no necesita) y Flask (validación, documentación y manejo de errores habría que armarlos
a mano).

### 2.1 Base de datos

> **Cambio del 2026-10-15:** se reemplaza MySQL por PostgreSQL (decisión del usuario).

- El host MySQL indicado en el enunciado (`prueba.cluster-...rds.amazonaws.com`) **no resuelve en DNS**
  (verificado el 2026-10-15).
- Bluecore dispone de un cluster **Aurora PostgreSQL 16** (base `demo`) donde cada candidato tiene su propio
  esquema. Al usuario `usuario_a` le corresponde **`esquema_a`**, el único donde puede crear objetos.
- **Solo se trabaja con `esquema_a`**: la aplicación no lee ni modifica ningún otro esquema de esa base.
- Desarrollo local y `docker-compose`: **PostgreSQL 16 en Docker**, que reproduce el entorno de Bluecore
  (base `demo`, rol `usuario_a` sin privilegios de administrador, esquema `esquema_a`).
- La conexión fija `search_path = esquema_a`, así que las tablas no llevan el esquema escrito en el código.
  Apuntar a Aurora o a Docker es solo cambiar `DATABASE_URL` en `.env`.

## 3. Convenciones

- **Código, tablas y API en inglés** (estándar de la industria).
- **Todo lo que ve el usuario en español:** pantallas, mensajes de error y validación.
- **Comentarios en el código en español**, para aclarar decisiones puntuales.
- **Conventional Commits** (`feat:`, `fix:`, `test:`, `docs:`, `chore:`, `refactor:`), un cambio
  lógico por commit.

## 4. Reglas de negocio

### 4.1 Solicitud de crédito

| Campo | Regla |
|---|---|
| Monto (`amount`) | USD, entre **500.00 y 50,000.00** (ambos incluidos), máximo 2 decimales |
| Plazo (`term_months`) | Entero entre **6 y 60** meses (ambos incluidos) |
| Cédula (`applicant_document`) | Formato de cédula panameña (sección 4.2) |

Una solicitud **no se puede editar ni eliminar** una vez creada (se conserva como registro).

### 4.2 Cédula panameña

Formato: `<prefijo>-<tomo>-<asiento>`, con guiones obligatorios.

| Tipo | Prefijo | Ejemplo |
|---|---|---|
| Panameño | Provincia `1`–`13` | `8-430-70`, `12-1234-12345` |
| Serie antigua (antes de 2006) | Provincia `1`–`13` + `AV` | `10AV-1234-12345` |
| Población indígena | Provincia `1`–`13` + `PI` | `1PI-1234-12345` |
| Extranjero residente | `E` | `E-8-123456` |
| Naturalizado | `N` | `N-1234-12345` |
| Panameño nacido en el extranjero | `PE` | `PE-5-687` |

- **Tomo:** 1 a 4 dígitos. **Asiento:** 1 a 6 dígitos.
- Provincias: 10 provincias y 3 comarcas con rango provincial (13 = Panamá Oeste). `14` es inválido.
- Antes de validar se **normaliza**: se eliminan espacios y se pasa a mayúsculas (`pe-5-687` → `PE-5-687`).
- Los guiones son obligatorios porque sin ellos el valor es ambiguo (`8430700` puede ser `8-430-700` u `84-30-700`).
- Se guarda como texto ya normalizado.
- La regla vive en **una sola función** con sus tests, para que un cambio de regla toque un solo lugar.

Expresión regular de referencia (sobre el valor normalizado):

```
^(?:(?:[1-9]|1[0-3])(?:AV|PI)?|E|N|PE)-\d{1,4}-\d{1,6}$
```

### 4.3 Estados y transiciones

```
PENDING ──► APPROVED
   │
   └─────► REJECTED
```

- Toda solicitud nace en `PENDING`.
- Solo una solicitud `PENDING` puede pasar a `APPROVED` o `REJECTED`.
- **La decisión es final:** decidir sobre una solicitud ya decidida responde `409 Conflict`.
- Aprobar y rechazar **requieren comentario** de 5 a 500 caracteres (se recortan espacios al inicio y al final).
- En pantalla: `PENDING` = "Pendiente", `APPROVED` = "Aprobada", `REJECTED` = "Rechazada".

**Concurrencia:** el cambio de estado se hace con una actualización atómica condicionada
(`UPDATE ... WHERE id = :id AND status = 'PENDING'`). Si no afecta ninguna fila y la solicitud existe,
otro usuario ya la decidió y se responde `409`. Así una solicitud nunca queda aprobada y rechazada a la vez.

## 5. Modelo de datos

Tabla única `credit_applications`:

| Columna | Tipo | Notas |
|---|---|---|
| `id` | `VARCHAR(36)`, PK | UUID v4 generado por la aplicación; no expone volumen ni permite adivinar IDs. Texto (y no el tipo `uuid` nativo) para que el mismo modelo funcione en los tests con SQLite |
| `applicant_document` | `VARCHAR(20)`, NOT NULL | Cédula normalizada |
| `amount` | `NUMERIC(10,2)`, NOT NULL | Nunca `float` para dinero |
| `term_months` | `SMALLINT`, NOT NULL | |
| `status` | `VARCHAR(10)`, NOT NULL, default `PENDING` | |
| `decision_comment` | `TEXT`, NULL | |
| `decided_at` | `TIMESTAMP`, NULL | UTC |
| `created_at` | `TIMESTAMP`, NOT NULL | UTC |
| `updated_at` | `TIMESTAMP`, NOT NULL | UTC |

- **Restricciones `CHECK`** en la base (defensa en profundidad): `amount BETWEEN 500 AND 50000`,
  `term_months BETWEEN 6 AND 60`, `status IN ('PENDING','APPROVED','REJECTED')`.
- **Índice** en `status` (filtro del listado) y en `created_at` (ordenamiento).
- **Sin tabla de historial:** como la decisión es final, cada solicitud cambia de estado una sola vez;
  el comentario y la fecha de decisión caben en la misma fila. Si en el futuro se permiten más
  transiciones, se agrega una tabla de historial.
- El esquema se crea con una **migración de Alembic**, no con `create_all`.

## 6. API

Prefijo: **`/api/v1`**. JSON en `snake_case`. Documentación interactiva en `/docs`.

| Método y ruta | Descripción | Éxito |
|---|---|---|
| `POST /api/v1/credit-applications` | Crear solicitud | `201 Created` + cabecera `Location` + solicitud |
| `GET /api/v1/credit-applications` | Listar (filtro y paginación) | `200 OK` |
| `GET /api/v1/credit-applications/{id}` | Obtener una solicitud | `200 OK` |
| `PATCH /api/v1/credit-applications/{id}/status` | Aprobar o rechazar con comentario | `200 OK` + solicitud actualizada |
| `GET /health` | Estado de la API y de la base de datos | `200 OK` / `503` |

### 6.1 Crear

```http
POST /api/v1/credit-applications
Content-Type: application/json

{ "applicant_document": "8-430-70", "amount": 15000.00, "term_months": 24 }
```

### 6.2 Representación de una solicitud

```json
{
  "id": "3f1c9a52-6a3e-4c55-9a4e-2d6b1f0e8c11",
  "applicant_document": "8-430-70",
  "amount": 15000.00,
  "term_months": 24,
  "status": "PENDING",
  "decision_comment": null,
  "decided_at": null,
  "created_at": "2026-10-15T21:30:00Z",
  "updated_at": "2026-10-15T21:30:00Z"
}
```

- `amount` se maneja internamente como `Decimal` y se serializa como número con 2 decimales.
- Las fechas van en ISO 8601 y UTC.

### 6.3 Listar

```http
GET /api/v1/credit-applications?status=PENDING&limit=20&offset=0
```

```json
{ "items": [ ... ], "total": 57, "limit": 20, "offset": 0 }
```

- `status` es opcional; si se envía debe ser `PENDING`, `APPROVED` o `REJECTED` (si no, `422`).
- `limit`: por defecto 20, mínimo 1, máximo 100. `offset`: por defecto 0, mínimo 0.
- Orden: `created_at` descendente (más recientes primero).

### 6.4 Cambiar estado

```http
PATCH /api/v1/credit-applications/{id}/status
Content-Type: application/json

{ "status": "REJECTED", "comment": "Capacidad de pago insuficiente" }
```

- `status` solo admite `APPROVED` o `REJECTED`.

### 6.5 Justificación de diseño

- Recursos como sustantivos en plural; la acción la indica el método HTTP.
- `PATCH /{id}/status` en lugar de `PUT /{id}`: no se reemplaza el recurso, solo cambia su estado,
  y deja explícito que monto, plazo y cédula no son editables.
- Un solo endpoint para aprobar y rechazar en lugar de `/approve` y `/reject`: es la misma operación
  con distinto valor; evita duplicar lógica.
- Sin `DELETE`: en el sector financiero las solicitudes se conservan como registro.
- Listado paginado: en un sistema real la tabla crece.
- API versionada (`/v1`) para poder evolucionarla sin romper clientes.

## 7. Manejo de errores

Todos los errores, sin excepción, usan el formato **RFC 9457 (Problem Details)** con
`Content-Type: application/problem+json` y textos en español:

```json
{
  "type": "validation_error",
  "title": "Datos inválidos",
  "status": 422,
  "detail": "La solicitud contiene datos inválidos.",
  "errors": [
    { "field": "amount", "message": "El monto debe estar entre $500.00 y $50,000.00." },
    { "field": "applicant_document", "message": "La cédula no tiene un formato válido. Ejemplo: 8-430-70." }
  ]
}
```

- `title` y `detail`: mensajes legibles que el frontend muestra tal cual.
- `errors`: solo en errores de validación; detalle por campo para mostrarlo junto a cada campo.
- `type`: código estable para lógica del frontend.

| Código | Cuándo | `type` |
|---|---|---|
| 400 | El cuerpo no es JSON válido | `malformed_request` |
| 404 | La solicitud o la ruta no existe | `not_found` |
| 409 | Se decide sobre una solicitud ya decidida | `application_already_decided` |
| 422 | JSON válido que no cumple las reglas (monto, plazo, cédula, comentario, estado, `id` mal formado, parámetros de consulta) | `validation_error` |
| 500 | Error inesperado | `internal_error` |
| 503 | La base de datos no responde (`/health`) | `service_unavailable` |

- Los mensajes de validación de Pydantic se traducen a mensajes propios en español.
- El `500` nunca expone trazas ni detalles internos; el detalle técnico solo va a los logs.
- 422 (no 400) para validaciones: el JSON es correcto pero viola las reglas; 400 se reserva para JSON ilegible.
- 409 para "ya decidida": los datos son válidos pero chocan con el estado actual del recurso.

## 8. Arquitectura

### 8.1 Backend: capas

```
backend/
├── app/
│   ├── main.py            ← crea la app FastAPI, registra routers y handlers de errores
│   ├── api/               ← endpoints: traducen HTTP ⇄ servicios (sin reglas de negocio)
│   ├── schemas/           ← modelos Pydantic: contrato de entrada y salida
│   ├── services/          ← reglas de negocio (transiciones de estado, normalización)
│   ├── domain/            ← reglas puras sin dependencias (validación de cédula, estados)
│   ├── repositories/      ← acceso a datos con SQLAlchemy
│   ├── models/            ← modelos ORM (tablas)
│   └── core/              ← configuración (.env), sesión de BD, errores y handlers
├── alembic/               ← migraciones
├── tests/
├── requirements.txt
└── .env.example
```

- Las reglas de negocio no conocen HTTP ni la base de datos: se prueban sin servidor ni base.
- Los servicios lanzan **excepciones de dominio** (`ApplicationNotFound`, `ApplicationAlreadyDecided`);
  los handlers de `core/` las convierten en respuestas Problem Details. Los endpoints no arman errores a mano.
- Configuración con variables de entorno (`DATABASE_URL`, orígenes CORS) leídas desde `.env`.

**Flujo de una petición:** `api` (valida forma con `schemas`) → `services` (aplica reglas de negocio)
→ `repositories` (persiste con `models`) → respuesta serializada con `schemas`.

### 8.2 Frontend

```
frontend/src/app/
├── core/          ← servicio de la API, interceptor de errores, modelos (tipos)
├── features/credit-applications/
│   ├── application-list/     ← listado con filtros, paginación y acciones
│   ├── application-form/     ← creación de solicitud
│   └── decision-dialog/      ← aprobar o rechazar con comentario obligatorio
└── shared/        ← componentes reutilizables (etiqueta de estado, mensajes de error)
```

**Pantallas:**

- **Listado** (`/solicitudes`, ruta inicial): filtros Todas / Pendientes / Aprobadas / Rechazadas;
  tabla con fecha, cédula, monto, plazo y estado; botones Aprobar / Rechazar solo en solicitudes
  pendientes; paginación anterior/siguiente.
- **Nueva solicitud** (`/solicitudes/nueva`): cédula (con ejemplo), monto (USD) y plazo (meses).
  Al crear, vuelve al listado con un mensaje de confirmación.
- **Diálogo de decisión:** confirma la acción y exige el comentario. Si la API responde `409`,
  muestra el mensaje y recarga el listado.

**Decisiones:**

- Validación en el formulario solo para mejorar la experiencia; la que manda es la del backend.
  Los errores de `errors[]` se muestran junto a cada campo.
- Interceptor HTTP centralizado que convierte cualquier error en un mensaje legible; si no hay
  conexión: "No se pudo conectar con el servidor".
- Reactive Forms. Sin librerías de componentes; CSS propio.
- Formato regional: `$15,000.00`, fechas `dd/mm/aaaa`.
- En desarrollo, un proxy de Angular redirige `/api` al backend; el backend también configura CORS.

## 9. Fases de trabajo

1. **Base del repositorio:** `.gitignore`, `.env.example`, retirar el PDF con credenciales,
   `docker-compose.yml` solo con PostgreSQL.
2. **Backend:** modelo, migración, validaciones, endpoints, manejo de errores y tests.
3. **Frontend:** Angular conectado al backend real.
4. **README** completo y verificación de que todo corre desde cero siguiendo el README.
5. **Bonus:** dockerizar backend y frontend (`docker-compose up` levanta todo).
6. **Bonus:** autenticación JWT básica (login + token).

Las fases 5 y 6 se diseñan en detalle cuando las fases 1–4 estén completas y verificadas.

## 10. Tests

**Backend (pytest):**

- Validación de cédula: casos válidos e inválidos por tipo (`8-430-70`, `10AV-1234-12345`,
  `PE-5-687`, `E-8-123456`, provincia `14`, sin guiones, letras inválidas, minúsculas normalizadas).
- Límites de negocio: monto 499.99 ❌, 500 ✅, 50,000 ✅, 50,000.01 ❌, 3 decimales ❌;
  plazo 5 ❌, 6 ✅, 60 ✅, 61 ❌.
- Transiciones: aprobar o rechazar una pendiente ✅; decidir una ya decidida → 409;
  comentario vacío o muy corto → 422; estado `PENDING` como destino → 422.
- Endpoints completos con `TestClient` sobre SQLite en memoria (los tests corren sin Docker ni PostgreSQL),
  incluyendo el formato Problem Details de los errores y el filtro y paginación del listado.

**Frontend:** validación del formulario e interceptor de errores.

## 11. Configuración, seguridad y entrega

- Credenciales solo en `.env` (ignorado por Git); en el repo, `.env.example` con valores de ejemplo.
- Retirar `Prueba_Bluecore.pdf` del repositorio (contiene credenciales) e ignorar la copia en `docs/`.
  Si el commit inicial ya está publicado, evaluar reescribir el historial (tiene un solo commit).
- `docker-compose.yml` en la raíz, inicialmente solo con PostgreSQL.
- `db.txt` (DDL de la base `demo` de Bluecore) no se versiona: expone la estructura interna de Bluecore.
- Entrega: repositorio público en GitHub con `/backend`, `/frontend`, `docker-compose.yml` y `README.md`.
- **README:** descripción, requisitos previos, cómo correr cada parte paso a paso, cómo correr los
  tests, tabla de endpoints con ejemplos y sección "Decisiones de diseño".
