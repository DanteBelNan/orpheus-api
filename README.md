# Orpheus API

API REST de Project Orpheus. Construida con **Python + FastAPI**, base de datos **MySQL**, completamente dockerizada.

---

## Stack

- Python 3.12
- FastAPI + Uvicorn
- SQLAlchemy (async) + aiomysql
- python-jose (firma y validación de JWT)
- Docker + docker-compose

---

## Esquema de Base de Datos

### `users`
| Column | Type | Notes |
|---|---|---|
| id | INT PK AUTO_INCREMENT | |
| email | VARCHAR(255) UNIQUE | Obtenido de Spotify `GET /v1/me` — requiere scope `user-read-email` |
| spotify_user_id | VARCHAR(255) | Obtenido de Spotify `GET /v1/me` — identificador único del usuario en Spotify |
| spotify_refresh_token | TEXT | MVP: almacenado en DB; Post-MVP: cifrado en reposo |
| spotify_access_token | TEXT | De corta duración, cacheado |
| token_expires_at | DATETIME | Utilizado por el middleware de refresco de token |
| created_at | DATETIME | |

### `devices`
| Column | Type | Notes |
|---|---|---|
| id | INT PK AUTO_INCREMENT | |
| device_id | VARCHAR(255) UNIQUE | MAC address de la Raspberry Pi |
| user_id | INT FK → users.id | |
| spotify_device_id | VARCHAR(255) | ID interno de Spotify del dispositivo Raspotify, cacheado |
| name | VARCHAR(255) | Nombre descriptivo (ej. "Orpheus #1") |
| last_seen | DATETIME | Actualizado en cada heartbeat |
| created_at | DATETIME | |

### `vinyls`
| Column | Type | Notes |
|---|---|---|
| id | INT PK AUTO_INCREMENT | Identificador interno de DB |
| tag_id | VARCHAR(255) UNIQUE | UID de fábrica del chip RFID — inmutable, enviado por la Pi |
| created_by | INT FK → users.id | Usuario dueño del dispositivo que escaneó el tag por primera vez. Único autorizado para asignar o modificar el `spotify_uri` |
| name | VARCHAR(255) nullable | Asignado por el creador desde la web. NULL mientras esté pendiente |
| spotify_uri | VARCHAR(255) nullable | e.g. `spotify:album:xxx`. NULL = vinilo pendiente de configuración |
| album_name | VARCHAR(255) nullable | Populado al asignar el álbum |
| album_art_url | TEXT nullable | Populado al asignar el álbum |
| created_at | DATETIME | |
| last_played | DATETIME | |

---

## Endpoints

### Auth — Spotify OAuth 2.0

#### `GET /auth/login`
Redirige al usuario a la página de autorización de Spotify.
- **Scopes solicitados:** `user-read-email`, `user-read-playback-state`, `user-modify-playback-state`, `streaming`
- **Respuesta:** 302 redirect a Spotify

#### `GET /auth/exchange?code=...`
Spotify redirige aquí tras la aprobación del usuario.
- Intercambia el `code` por `access_token` + `refresh_token`
- Llama a `GET /v1/me` de Spotify para obtener `spotify_user_id` y `email`
- **Upsert** en tabla `users`: crea el usuario si es nuevo, actualiza tokens si ya existe
- Genera un **JWT** firmado con `SECRET_KEY` conteniendo `{ user_id, exp }`
- Setea el JWT como cookie `httpOnly` + `SameSite=Lax`. En producción debe configurarse también `Secure`.
- **Respuesta:** `{ "message": "Authenticated successfully", "user": { "id": 1, "email": "...", "spotify_user_id": "...", "created_at": "..." } }`

#### `GET /auth/me`
Devuelve el usuario autenticado actual a partir de la cookie JWT. Usado por el frontend para restaurar sesión al recargar la app.
- **Auth:** sesión de usuario requerida
- **Respuesta:** `{ "id": 1, "email": "...", "spotify_user_id": "...", "created_at": "..." }` → 200
- **Respuesta (sin sesión o token inválido):** 401

---

### Device

#### `GET /devices/`
Devuelve todos los dispositivos registrados bajo el usuario autenticado.
- **Auth:** sesión de usuario requerida
- **Respuesta:** `{ "devices": [{ "id": 1, "device_id": "...", "name": "...", "last_seen": "...", "spotify_device_id": "..." }], "amount": 1 }`

#### `GET /devices/{device_id}`
Devuelve el detalle de un dispositivo específico por su MAC address.
- **Auth:** sesión de usuario requerida
- **Respuesta:** `{ "id": 1, "device_id": "b8:27:eb:xx:xx:xx", "name": "...", "last_seen": "...", "spotify_device_id": "..." }` → 200
- **Respuesta (no encontrado):** 404

#### `POST /devices/`
Registra una Raspberry Pi bajo la cuenta de un usuario.
- **Auth:** sesión de usuario requerida
- **Request:** `{ "device_id": "b8:27:eb:xx:xx:xx", "name": "Orpheus #1" }`
- **Respuesta:** `{ "id": 1, "device_id": "...", "name": "..." }` → 201
- **Respuesta (device ya registrado):** 409

#### `POST /devices/heartbeat`
Llamado por la Pi en cada arranque. Actualiza `last_seen` y refresca el `spotify_device_id` consultando la lista de dispositivos activos en Spotify. El `spotify_device_id` se cachea para reducir latencia, pero Spotify no garantiza que sea permanente; si falla playback por dispositivo no encontrado/restringido, el backend debe refrescarlo y reintentar.
- **Auth:** `X-Device-Key` header — shared key embebida en el binario de la Pi en compilación
- **Request:** `{ "device_id": "b8:27:eb:xx:xx:xx" }`
- **Respuesta:** `{ "status": "ok", "spotify_device_id": "abc123" }`
- **Respuesta (key inválida):** 401

#### `GET /devices/auth?device_id=...`
Llamado por el binario al boot y cada 55 minutos para obtener un access token fresco sin almacenar credenciales en el dispositivo. El backend refresca el token del usuario asociado al device si está por vencer y devuelve el token vigente.
- **Auth:** `X-Device-Key` header
- **Respuesta:** `{ "access_token": "BQC...", "device_name": "Orpheus", "expires_at": "2026-08-09T15:00:00" }` → 200
- **Respuesta (device no registrado):** 404
- **Respuesta (error de Spotify):** 502

---

### Resources

#### `GET /resources/search?q={query}&resource_type=album,playlist`
Proxy hacia la Spotify Search API. El backend realiza la búsqueda usando el `access_token` del usuario autenticado y devuelve los resultados al frontend. `resource_type` defaultea a `"album,playlist"` si no se especifica.
- **Auth:** sesión de usuario requerida
- **Respuesta:** `[{ "spotify_uri": "spotify:album:xxx", "name": "...", "art_url": "...", "resource_type": "album|playlist", "artist": "..." }]`

---

### Vinyls

#### `GET /vinyls/{id}`
Devuelve el detalle completo de un vinilo.
- **Auth:** sesión de usuario requerida
- **Respuesta:** `{ "id": 1, "tag_id": "04:A2:B3:C4", "name": "...", "spotify_uri": "...", "album_name": "...", "album_art_url": "...", "status": "pending|configured", "created_by": 3 }` → 200
- **Respuesta (no encontrado):** 404

#### `GET /vinyls`
Devuelve todos los vinilos del sistema. Cualquier usuario autenticado puede navegar el catálogo completo.
- **Auth:** sesión de usuario requerida
- **Query params:** `?created_by={user_id}` para filtrar por creador (opcional), `?status=pending|configured` (opcional)
- **Respuesta:** `[{ "id": 1, "tag_id": "04:A2:B3:C4", "name": "...", "album_name": "...", "album_art_url": "...", "spotify_uri": "...", "status": "configured", "created_by": 3 }]`
- El campo `status` se deriva: `pending` si `spotify_uri` es NULL, `configured` en caso contrario

#### `PATCH /vinyls/{id}`
Asigna un álbum o playlist a un vinilo pendiente. Restringido al usuario `created_by`.
- **Auth:** sesión de usuario requerida
- **Autorización:** devuelve `403` si el usuario autenticado no es el `created_by`
- **Request:** `{ "name": "Road Trips Mix", "spotify_uri": "spotify:album:xxx", "album_name": "...", "album_art_url": "..." }`
- **Respuesta:** `{ "id": 1, "tag_id": "...", "name": "...", "status": "configured", ... }` → 200

#### `DELETE /vinyls/{id}`
Elimina un vinilo. Solo el creador puede eliminar los suyos.
- **Auth:** sesión de usuario requerida
- **Autorización:** devuelve `403` si el usuario autenticado no es el `created_by`
- **Respuesta:** 204 No Content

---

### Playback

#### `POST /play`
Endpoint principal. Llamado por la Raspberry Pi al leer un tag. Implementa la lógica **Register or Play**.

- **Auth:** `X-Device-Key` header — shared key embebida en el binario de la Pi en compilación
- **Request:** `{ "device_id": "b8:27:eb:xx:xx:xx", "tag_id": "04:A2:B3:C4" }`
- **Flujo:**
  1. Busca el `device_id` → identifica al usuario dueño del dispositivo
  2. Busca el `tag_id` en la tabla `vinyls` (búsqueda global)
  3. **Caso 1 — Tag nuevo:** crea registro en `vinyls` con `spotify_uri = NULL`, `created_by = device owner` → responde 201 *(Pi reproduce chime)*
  4. **Caso 2 — Tag pendiente** (`spotify_uri` es NULL): responde 202 *(Pi reproduce sonido de pendiente)*
  5. **Caso 3 — Tag configurado:** token middleware refresca el `access_token` del device owner si está vencido → llama `PUT /v1/me/player/play` en Spotify con el `spotify_uri` del vinilo y el `spotify_device_id` cacheado del dispositivo → responde 200
- **Response (nuevo):** `{ "status": "registered", "vinyl_id": 7 }` → 201
- **Response (pendiente):** `{ "status": "pending", "vinyl_id": 7 }` → 202
- **Response (reproduciendo):** `{ "status": "playing", "vinyl": { "name": "...", "album": "...", "art_url": "...", "spotify_uri": "..." } }` → 200
- **Response (device no registrado):** `{ "detail": "Device not found" }` → 404 *(Pi reproduce sonido de error)*
- **Response (Spotify o Raspotify offline):** `{ "detail": "..." }` → 502 *(Pi reproduce sonido de error)*

#### `GET /play/state?device_id=...`
Devuelve el estado de reproducción actual del dispositivo consultando directamente la API de Spotify. Usado por el display del binario para mostrar el track en curso.
- **Auth:** `X-Device-Key` header
- **Respuesta:** `{ "is_playing": true, "track_name": "Money", "artist_name": "Pink Floyd", "album_name": "The Dark Side of the Moon", "current_track": 6, "total_tracks": 10, "duration": 382000, "progress": 30000 }` → 200
- **Respuesta (nada reproduciéndose):** misma estructura con `is_playing: false` y campos en defaults
- **Respuesta (device no registrado):** 404
- **Respuesta (error de Spotify):** 502

---

## Middleware

### Token Refresh Middleware
Intercepta cada request que requiere interacción con Spotify. Antes de llamar a Spotify:
1. Lee `token_expires_at` de la DB para el usuario correspondiente
2. Si está vencido (o dentro de los 60s previos al vencimiento), llama a `POST https://accounts.spotify.com/api/token` con el `refresh_token` almacenado
3. Actualiza `access_token` y `token_expires_at` en DB
4. Continúa con el request original

Esto garantiza cero re-autenticaciones manuales para el usuario final.

---

## Docker Setup

### Correr localmente

```bash
cp .env.example .env
# Completar con Spotify Client ID, Client Secret y credenciales de DB

docker-compose up --build
```

API disponible en `http://localhost:8000`
Documentación automática en `http://localhost:8000/docs`

### Variables de Entorno

| Variable | Descripción |
|---|---|
| `SPOTIFY_CLIENT_ID` | Desde el Spotify Developer Dashboard |
| `SPOTIFY_CLIENT_SECRET` | Desde el Spotify Developer Dashboard |
| `SPOTIFY_REDIRECT_URI` | URL registrada en Spotify para volver al frontend, ej. `http://localhost:5173/auth/callback` |
| `MYSQL_HOST` | Host de la DB (usar `db` dentro de docker-compose) |
| `MYSQL_PORT` | Por defecto 3306 |
| `MYSQL_USER` | Usuario de la DB |
| `MYSQL_PASSWORD` | Contraseña de la DB |
| `MYSQL_DATABASE` | Nombre de la base de datos (ej. `orpheus`) |
| `SECRET_KEY` | Para firma de JWT (HS256) |
| `JWT_EXPIRE_HOURS` | Duración del JWT en horas (por defecto: 12) |
| `CORS_ORIGINS` | Origins permitidos para el frontend, separados por coma (ej. `http://localhost:5173,http://127.0.0.1:5173`) |

---

## Post-MVP: Reanudar Vinilo desde donde se quedó

Cuando se reproduce un vinilo, guardar en la tabla `vinyls` la canción y el timestamp en el que se dejó de escuchar (`last_song_index`, `last_position_ms`). La próxima vez que se escanee ese tag, el endpoint `POST /play` pasaría esos valores al cliente de Spotify (`offset.position` y `position_ms`) en lugar de arrancar desde el inicio.

El `SpotifyClient.play()` ya acepta `song_index` y `ms_delay` como parámetros opcionales con defaults en 0, dejando la puerta abierta para esta feature sin cambios de interfaz.

---

## Estado actual del código

- Implementado: OAuth Spotify con `/auth/login`, `/auth/exchange` y `/auth/me`.
- Implementado: sesión con JWT en cookie `httpOnly` y `SameSite=Lax`; falta activar `Secure` para producción.
- Implementado: endpoints de dispositivos, vinilos, búsqueda de recursos y `/play`.
- Implementado: `/play` resuelve la MAC address al dispositivo registrado, usa el `spotify_device_id` cacheado y exige que exista solo cuando el vinilo ya está configurado.
- Implementado: `GET /devices/{device_id}` valida que el dispositivo consultado pertenezca al usuario autenticado.
- Gap Post-MVP: si Spotify rechaza playback por dispositivo no encontrado/restringido, el backend debe refrescar `spotify_device_id` desde `GET /v1/me/player/devices` y reintentar una vez.

---

## Post-MVP: Seguridad de Tokens Spotify

Cifrar en reposo `spotify_refresh_token` y cualquier token persistido en DB. El MVP usa almacenamiento directo en base de datos para avanzar rápido, pero el despliegue público debería incorporar cifrado antes de ampliar usuarios.

---

## Post-MVP: Identidad Dinámica de Dispositivo

Reemplazar el `X-Device-Key` compartido por una credencial por dispositivo, idealmente emitida durante un flujo de pairing. Una opción posible es que cada Raspberry tenga un secreto propio y obtenga tokens firmados de corta duración para llamar a `/play` y `/devices/heartbeat`.

---

## Post-MVP: Historial de Asignaciones de Vinilos

Cada vez que un usuario configura o reconfigura un vinilo (vía `PATCH /vinyls/{id}`), el sistema podría registrar un historial de cambios en una tabla `vinyl_history`. Esto permitiría saber qué álbum estuvo asignado a un vinilo en cada momento, quién lo cambió y cuándo.

Esquema tentativo de la tabla:

| Column | Type | Notes |
|---|---|---|
| id | INT PK | |
| vinyl_id | INT FK → vinyls.id | |
| changed_by | INT FK → users.id | |
| previous_spotify_uri | VARCHAR(255) nullable | URI anterior, NULL si es la primera asignación |
| new_spotify_uri | VARCHAR(255) | URI nueva asignada |
| changed_at | DATETIME | |

El repository de vinyls ya tiene un comentario reservado para esta funcionalidad en el método `update`. La implementación consistiría en insertar un registro en `vinyl_history` dentro del mismo `update`, antes del commit.

---

## Post-MVP: Biblioteca de Recursos Precargados (Playlists)

Permite al usuario guardar álbumes y playlists de Spotify localmente para tenerlos como acceso rápido al configurar vinyls, sin tener que buscar en Spotify cada vez. Requiere una tabla `playlists` y tres endpoints: `GET /playlists`, `POST /playlists`, `DELETE /playlists/{id}`. Descartado del MVP por no agregar valor crítico — si Spotify no devuelve un URI válido al buscarlo, tampoco lo devuelve guardado localmente.

---

## Post-MVP: Servicio de Notificaciones por Email

Cuando `/play` registra un tag nuevo (201), publicará un evento asincrónico para notificar al `created_by` por email. El mecanismo concreto de cola/worker queda a definir (opciones: background tasks nativas de FastAPI, Redis pub/sub, u otro mecanismo liviano), pero el contrato es claro: la API principal no bloquea la respuesta a la Pi esperando el envío del email. El worker consume el evento de forma independiente y envía via AWS SES o SendGrid con el mensaje: *"Detectamos un nuevo mini-vinilo en tu dispositivo Orpheus. Ingresá a la plataforma cuando quieras para asociarle tu álbum favorito."*
