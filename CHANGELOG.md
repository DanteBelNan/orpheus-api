# Changelog

All notable changes to the Orpheus API are documented here.

## Versioning convention

| Version | Meaning |
|---|---|
| `0.x.0` | New module added during development |
| `1.0.0` | Complete MVP — all modules integrated and working end-to-end |
| `2.0.0` | First production-ready release |

---
## [Unreleased]
---
## [1.0.0] - 2026-07-19 — MVP Completo

### Added
- `app/services/play_service.py` — lógica Register or Play: tag nuevo → crea
  vinilo + lanza `VinylCreated` (201), tag pendiente → lanza `VinylPending` (202),
  tag configurado → refresca token + llama `SpotifyService.play()` → 200
- `app/clients/spotify_client.py::play()` — `PUT /v1/me/player/play` con
  `device_id` como query param y `context_uri`, `offset.position`, `position_ms`
  en el body. Soporta `song_index` y `ms_delay` para futura feature de reanudación
- `app/services/spotify_service.py::play()` — delegación al client con
  `@with_fresh_token` decorator
- `app/exceptions/base_exception.py` — `PendingError` y `Registered` como bases
- `app/exceptions/vinyl_exception.py` — `VinylCreated`, `VinylPending`
- `app/dtos/play_dto.py` — `PlayRequest` con `device_id` y `tag_id`
- `app/controllers/play_controller.py` — `POST /play/` sin JWT, busca device →
  user, maneja 3 casos via `JSONResponse` (200/201/202) y 502 para fallos de Spotify
- `tests/test_play_service.py` — 9 tests cubriendo los 3 casos del Register or Play

- `app/logger.py` — logger JSON estructurado con fallback stdlib. Logs en
  `auth_service`, `device_service`, `spotify_service`, `play_service`,
  `vinyl_service` y `dependencies` (warning en device key inválida)
- `app/clients/spotify_client.py` — `exchange_code()` y `get_user_profile()`.
  URLs hardcodeadas reemplazadas por variables de `settings`
- `app/dependencies.py` — `verify_device_key` dependency para `X-Device-Key` header
- `app/main.py` — startup check de conexión a DB con log de éxito o error
- `app/config.py` — `spotify_auth_url`, `spotify_token_url`, `spotify_api_url`,
  `spotify_scopes`, `device_api_key` en Settings
- `tests/test_auth_service.py` — 73 tests pasando con mocks de `SpotifyClient`
- `db/init.sql` — script de inicialización de DB con las tres tablas (`users`,
  `devices`, `vinyls`) con sus constraints y foreign keys
- `docs/database.puml` — diagrama ER de las tres tablas con relaciones y notas
- `docs/architecture.puml` — diagrama de arquitectura mostrando los tres tipos
  de auth (JWT / X-Device-Key / público), flujos de comunicación y integración
  con Spotify

### Changed
- README: Alembic removido del stack, `resource_type` corregido en Resources,
  respuesta 503 corregida a 502 en Playback, auth de endpoints documentada
  (JWT / X-Device-Key / público)
- `app/main.py` — play router registrado
- `auth_service.py` — delega HTTP a `SpotifyClient`, elimina `httpx` y constantes
- `auth_controller.py` — inyecta `SpotifyClient`
- `POST /devices/heartbeat` y `POST /play` — requieren `X-Device-Key` header

---
## [0.4.2] - 2026-07-18

### Added
- `app/dtos/resource_dto.py` — `ResourceResponse` (spotify_uri, name, art_url,
  resource_type, artist) y `ResourceListResponse` para normalizar resultados
  de albums y playlists en una estructura uniforme
- `app/controllers/resource_controller.py` — `GET /resources/search?q=&resource_type=`
  proxy hacia Spotify Search API. `resource_type` defaultea a `"album,playlist"`.
  Maneja `ExternalServiceError` → 502
- `SpotifyService.search()` ahora parsea el dict crudo de Spotify y devuelve
  `ResourceListResponse` — normaliza albums y playlists extrayendo uri, name,
  art_url, artist
- `app/tests/test_spotify_client.py` — 10 tests unitarios cubriendo los 3
  métodos del client: `exchange_token`, `get_active_devices`, `search`. Cubre
  happy path, parámetros enviados y propagación de errores con status code

### Changed
- `main.py` — resource router registrado
- `spotify_service.py` — corregido default de `items` de `{}` a `[]` en el
  loop de albums del método `search`
- `test_spotify_service.py::TestSearch` — actualizado para verificar
  `ResourceListResponse` en lugar del dict crudo

---
## [0.4.1] - 2026-07-18

### Added
- `app/clients/spotify_client.py` — capa HTTP pura para Spotify API:
  `exchange_token`, `get_active_devices`, `search`. Cada método captura
  `httpx.HTTPStatusError` y propaga el mensaje de error de Spotify con
  status code incluido
- `with_fresh_token` decorator en `SpotifyService` — middleware que verifica
  expiración del token antes de cada llamada a Spotify, refresca si es necesario
  y actualiza `access_token` + `refresh_token` (si Spotify devuelve uno nuevo)
  en DB. Elimina la necesidad de llamar a `ensure_fresh_token` explícitamente
- `search(user, query, resource_type)` en `SpotifyService` — endpoint de
  búsqueda Spotify pendiente de su controller

### Changed
- `SpotifyService` ya no hace llamadas HTTP directas — delega todo al
  `SpotifyClient`. Elimina imports de `httpx`, `settings` y `SpotifyError`
- `SpotifyService.__init__` ahora recibe `SpotifyClient` además de `UserRepository`
- Métodos del service reciben `user` como primer argumento en lugar de
  `access_token` — el decorator resuelve el token internamente
- `user_repository.update_tokens` acepta `refresh_token: str | None = None`
  para manejar rotación de refresh tokens
- `device_controller.py` actualizado para inyectar `SpotifyClient` en `SpotifyService`
- `tests/test_spotify_service.py` reescrito: mockea `SpotifyClient` en lugar
  de `httpx`, cubre decorator, `get_spotify_device_id` y `search` (14 tests nuevos)

---
## [0.4.0] - 2026-07-16

### Added
- `PATCH /vinyls/{vinyl_id}` — asigna álbum a un vinilo, restringido al
  `created_by` (403 si no es el dueño, 404 si no existe). Usa
  `model_dump(exclude_none=True)` para actualización parcial de campos
- `DELETE /vinyls/{vinyl_id}` — elimina un vinilo con la misma lógica de
  autorización, devuelve 204 sin body
- `vinyl_router` registrado en `main.py`
- 8 tests nuevos en `test_vinyl_service.py` cubriendo PATCH y DELETE:
  not found, forbidden y happy path para ambos métodos

### Changed
- `mock_vinyl_repository` en tests actualizado con `update` y `delete` como `AsyncMock`

---
## [0.3.5] - 2026-05-30
### Added
- `app/exceptions/base_exception.py` — `ForbiddenError` con mensaje
  parametrizado: "{entity} with id '{id}' cannot be modified by user '{user_id}'"
- `app/exceptions/vinyl_exception.py` — `VinylNotFoundError`, `VinylForbiddenError`
- `app/dtos/vinyl_dto.py` — `VinylResponse` (con `@computed_field status`
  derivado de `spotify_uri`), `VinylListResponse`, `VinylUpdateRequest`
  
---
## [0.3.4] - 2026-05-30

### Added
- `.github/workflows/unit-tests.yml` — GitHub Actions workflow para ejecutar
  unit tests en cada push/PR hacia master, main o develop. Incluye:
  - Servicio MySQL en el workflow para tests de integración
  - Reporte de cobertura con pytest-cov (HTML artifact)
  - Comentarios de referencia para segunda fase: Docker build → ECR push → EC2
    deploy via SSH (self-hosted runner como alternativa recomendada)

--- 
## [0.3.3] - 2026-05-30

### Added
- `app/models/vinyl.py` — modelo SQLAlchemy Vinyl con `tag_id` (UID hardware,
  UNIQUE), `created_by` (FK → users), campos nullable para configuración
  (`name`, `spotify_uri`, `album_name`, `album_art_url`) y `last_played`
  (datetime nullable, para tracking futuro de reproducciones)
- `app/repositories/vinyl_repository.py` — `get_by_id`, `get_by_tag_id`,
  `get_all` (con filtros opcionales `created_by` y `status` via query
  incremental), `create` (nombre opcional para registro desde Pi),
  `update` (via `setattr` + `**fields` para actualización parcial),
  `delete`
- README: sección Post-MVP con historial de asignaciones de vinilos
  (`vinyl_history`) y esquema tentativo de tabla

---
## [0.3.2] - 2026-05-30

### Added
- `app/services/spotify_service.py` — servicio compartido para interacciones
  con la Spotify API: `ensure_fresh_token` (refresca el access_token si venció
  y actualiza DB) y `get_spotify_device_id` (busca el dispositivo Raspotify
  por nombre en la lista de dispositivos activos de Spotify)
- `tests/test_spotify_service.py` — 9 tests cubriendo token válido, refresco
  de token expirado, actualización en DB, error de Spotify, y búsqueda de
  dispositivo por nombre

### Changed
- `device_service.py` — `DeviceService` ahora recibe `SpotifyService` como
  dependencia en lugar de tener los métodos privados `_ensure_fresh_token` y
  `_get_spotify_device_id`. Elimina imports de `httpx`, `settings` y `SpotifyError`
- `device_controller.py` — cadena de dependencias actualizada para instanciar
  e inyectar `SpotifyService`
- `tests/test_device_service.py` — refactorizado para usar `mock_spotify_service`
  en lugar de mockear `httpx` directamente. `TestEnsureFreshToken` y
  `TestGetSpotifyDeviceId` migrados a `test_spotify_service.py`

--- 
## [0.3.1] - 2026-05-30

### Added
- `app/exceptions/base_exception.py` — `ExternalServiceError` con mensaje
  parametrizado `"{service} error: {detail}"`
- `app/exceptions/spotify_exception.py` — `SpotifyError(ExternalServiceError)`
  para todos los fallos de comunicación con la API de Spotify

### Changed
- `auth_service.py` — `exchange_code` y `get_spotify_user` ahora capturan
  `httpx.HTTPStatusError` y re-lanzan `SpotifyError`
- `auth_controller.py` — `/exchange` captura `ExternalServiceError` → 502
- `device_service.py` — `_ensure_fresh_token` y `_get_spotify_device_id`
  siguen el mismo patrón con `SpotifyError`
- `device_controller.py` — `/heartbeat` captura `ExternalServiceError` → 502 

---
## [0.3.0] - 2026-05-29

### Added
- `POST /devices/heartbeat` — token refresh automático + descubrimiento
  del spotify_device_id via Spotify API, sin JWT (llamado por la Pi)
- `tests/test_device_service.py` — 10 tests adicionales cubriendo
  heartbeat, token refresh y descubrimiento de dispositivo Spotify

---
## [0.2.3] - 2026-05-29

### Added
- `app/exceptions/base_exception.py` — NotFoundError y AlreadyExistsError
  con mensaje parametrizado: "Entity with id 'x' not/already found"
- `app/exceptions/user_exception.py` — UserNotFoundError
- `app/dtos/device_dto.py` — DeviceHeartbeatRequest, DeviceHeartbeatResponse
- `app/repositories/device_repository.py` — update_heartbeat (actualiza
  spotify_device_id y last_seen)
- `app/repositories/user_repository.py` — update_tokens

### Changed
- device_exception.py — DeviceNotFoundError y DeviceAlreadyRegisteredError
  heredan de las bases y pasan el device_id al mensaje
- device_controller.py — usa NotFoundError y AlreadyExistsError como bases
  para los catches; inyecta UserRepository en DeviceService
- device_service.py — raise con identificadores; esqueleto de process_heartbeat

### Pending
- process_heartbeat: lógica de token refresh + llamada a Spotify API

---
## [0.2.2] - 2026-05-29

### Added
- `app/exceptions/device_exception.py` — domain exceptions layer:
  `DeviceAlreadyRegisteredError`, `DeviceNotFoundError`
- `app/controllers/device_controller.py` — tres endpoints:
  `GET /devices/` (lista devices del usuario autenticado),
  `GET /devices/{device_id}` (detalle por MAC address, 404 si no existe),
  `POST /devices/` (registra device, 409 si ya existe)
- Device router registrado en `app/main.py`
---

## [0.2.1] - 2026-05-29

### Added
- `app/models/device.py` — SQLAlchemy Device model (`devices` table) con FK a `users`
- `app/dtos/device_dto.py` — Pydantic DTOs: `DeviceResponse` (con `from_attributes=True`), `DevicesListResponse`
- `app/repositories/device_repository.py` — `insert`, `get_by_user_id`, `get_by_device_id`
- `app/services/device_service.py` — `create_device`, `get_devices_by_user_id`, `get_device_by_id`
- `GET /devices/` — lista todos los dispositivos del usuario autenticado (documentado en README)
- `GET /devices/{device_id}` — detalle de un dispositivo por MAC address (documentado en README)
- `POST /devices/` — registro de un nuevo dispositivo (documentado en README)

---

## [0.2.0] - 2026-05-28

### Added
- `GET /auth/login` — redirects user to Spotify OAuth authorization page
- `GET /auth/exchange?code=...` — exchanges Spotify OAuth code for JWT, sets httpOnly cookie
- `app/models/user.py` — SQLAlchemy User model (`users` table)
- `app/dtos/user_dto.py` — Pydantic DTOs: `SpotifyUserData`, `SpotifyTokenData`, `UserResponse`
- `app/repositories/user_repository.py` — `get_by_spotify_id`, `get_by_id`, `upsert`
- `app/services/auth_service.py` — Spotify OAuth flow, JWT generation, user upsert orchestration
- `app/controllers/auth_controller.py` — auth HTTP endpoints with full dependency injection chain
- `app/dependencies.py` — `get_current_user` dependency for JWT-protected endpoints
- `tests/test_auth_service.py` — 12 unit tests covering login URL, code exchange, user fetch, callback flow and JWT generation
- `pytest.ini` — pytest configuration with asyncio auto mode

### Changed
- `/auth/callback` renamed to `/auth/exchange` — backend no longer redirects to frontend, returns 200 with cookie instead (decoupling)
- `frontend_url` removed from `Settings` — backend is now fully decoupled from frontend URL
- `SPOTIFY_REDIRECT_URI` updated in `.env.example` to point to frontend (`http://localhost:5173/auth/callback`)
- `extra="ignore"` added to `Settings` config to silently discard env vars not declared in the model (e.g. `MYSQL_ROOT_PASSWORD`)

---

## [0.1.0] - 2026-05-28

### Added
- `app/main.py` — FastAPI app instance with `GET /ping` health check endpoint
- `app/config.py` — `Settings` class with pydantic-settings, reads `.env`, exposes `database_url` property
- `app/database.py` — async SQLAlchemy engine, `AsyncSessionLocal`, `Base`, `get_db` dependency
- `Dockerfile` — multi-stage build: `base`, `dev` (hot-reload), `test` (runs pytest), `production` (lean image)
- `docker-compose.yml` — local dev environment: `api` service (target: dev, volume mount) + `db` service (MySQL 8.0 with healthcheck)
- `requirements.txt` and `requirements-dev.txt`
- `.env.example` with all required environment variables
