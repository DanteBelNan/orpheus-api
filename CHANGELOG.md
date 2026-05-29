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
## [0.3.0] - 2026-05-29

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
