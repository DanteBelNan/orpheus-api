# Orpheus API

API REST de Project Orpheus. Construida con **Python + FastAPI**, base de datos **MySQL**, completamente dockerizada.

---

## Stack

- Python 3.12
- FastAPI + Uvicorn
- SQLAlchemy (async) + aiomysql
- Alembic (migraciones)
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
| spotify_refresh_token | TEXT | Almacenado encriptado |
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

### `playlists`
Recursos de Spotify (álbumes o playlists) precargados por el usuario. Usados como fuente local en `GET /resources/search` para no depender de Spotify en tiempo real al configurar un vinilo.

| Column | Type | Notes |
|---|---|---|
| id | INT PK AUTO_INCREMENT | |
| user_id | INT FK → users.id | Dueño del recurso precargado |
| spotify_uri | VARCHAR(255) | e.g. `spotify:album:xxx` o `spotify:playlist:xxx` |
| name | VARCHAR(255) | Nombre del álbum o playlist |
| art_url | TEXT | URL de la imagen de portada |
| type | ENUM('album','playlist') | Tipo de recurso |
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
- Setea el JWT como cookie `httpOnly` + `Secure`
- **Respuesta:** nos trae la cookie para que la agreguemos desde nuestro frontend

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
Llamado por la Pi en cada arranque. Actualiza `last_seen` y refresca el `spotify_device_id` consultando la lista de dispositivos activos en Spotify.
- **Request:** `{ "device_id": "b8:27:eb:xx:xx:xx" }`
- **Respuesta:** `{ "status": "ok", "spotify_device_id": "abc123" }`

---

### Resources

#### `GET /resources/search?q={query}&type=album,playlist`
Busca recursos de Spotify (álbumes y/o playlists) para asignar a un vinilo. Devuelve resultados combinados de dos fuentes, cada uno etiquetado con su origen para que el frontend los muestre diferenciados.
- **Auth:** sesión de usuario requerida
- **Fuentes:**
  - `spotify` — búsqueda en vivo contra la Spotify Search API
  - `local` — recursos precargados del usuario desde la tabla `playlists`
- **Respuesta:** `[{ "spotify_uri": "spotify:album:xxx", "name": "...", "art_url": "...", "type": "album|playlist", "source": "spotify|local" }]`

---

### Playlists (Recursos Precargados)

Permite al usuario guardar álbumes y playlists de Spotify en su cuenta de Orpheus. Al configurar un vinilo, estos recursos aparecen junto a los resultados en vivo de Spotify en `GET /resources/search`, sin depender de la disponibilidad de Spotify en ese momento.

#### `GET /playlists`
Devuelve todos los recursos precargados por el usuario autenticado.
- **Auth:** sesión de usuario requerida
- **Respuesta:** `[{ "id": 1, "spotify_uri": "...", "name": "...", "art_url": "...", "type": "album|playlist" }]`

#### `POST /playlists`
Guarda un recurso de Spotify en la lista local del usuario.
- **Auth:** sesión de usuario requerida
- **Request:** `{ "spotify_uri": "spotify:playlist:xxx", "name": "...", "art_url": "...", "type": "playlist" }`
- **Respuesta:** `{ "id": 1, ... }` → 201

#### `DELETE /playlists/{id}`
Elimina un recurso precargado. Solo el dueño puede eliminarlo.
- **Auth:** sesión de usuario requerida
- **Autorización:** devuelve `403` si el usuario autenticado no es el dueño
- **Respuesta:** 204 No Content

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

- **Request:** `{ "device_id": "b8:27:eb:xx:xx:xx", "tag_id": "04:A2:B3:C4" }`
- **Flujo:**
  1. Busca el `device_id` → identifica al usuario dueño del dispositivo
  2. Busca el `tag_id` en la tabla `vinyls` (búsqueda global)
  3. **Caso 1 — Tag nuevo:** crea registro en `vinyls` con `spotify_uri = NULL`, `created_by = device owner` → responde 201 *(Pi reproduce chime)*
  4. **Caso 2 — Tag pendiente** (`spotify_uri` es NULL): responde 202 *(Pi reproduce sonido de pendiente)*
  5. **Caso 3 — Tag configurado:** token middleware refresca el `access_token` del device owner si está vencido → llama `PUT /v1/me/player/play` en Spotify con el `spotify_uri` del vinilo y el `spotify_device_id` cacheado del dispositivo → responde 200
- **Response (nuevo):** `{ "status": "registered", "vinyl_id": 7 }` → 201
- **Response (pendiente):** `{ "status": "pending", "vinyl_id": 7 }` → 202
- **Response (reproduciendo):** `{ "status": "playing", "vinyl": "..." }` → 200
- **Response (device no registrado):** `{ "error": "device_not_found" }` → 404 *(Pi reproduce sonido de error)*
- **Response (Raspotify offline):** `{ "error": "device_offline" }` → 503 *(Pi reproduce sonido de error)*

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
| `SPOTIFY_REDIRECT_URI` | ej. `http://localhost:8000/auth/callback` |
| `MYSQL_HOST` | Host de la DB (usar `db` dentro de docker-compose) |
| `MYSQL_PORT` | Por defecto 3306 |
| `MYSQL_USER` | Usuario de la DB |
| `MYSQL_PASSWORD` | Contraseña de la DB |
| `MYSQL_DATABASE` | Nombre de la base de datos (ej. `orpheus`) |
| `SECRET_KEY` | Para firma de JWT (HS256) |
| `JWT_EXPIRE_HOURS` | Duración del JWT en horas (por defecto: 12) |

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

## Post-MVP: Servicio de Notificaciones por Email

Cuando `/play` registra un tag nuevo (201), publicará un evento asincrónico para notificar al `created_by` por email. El mecanismo concreto de cola/worker queda a definir (opciones: background tasks nativas de FastAPI, Redis pub/sub, u otro mecanismo liviano), pero el contrato es claro: la API principal no bloquea la respuesta a la Pi esperando el envío del email. El worker consume el evento de forma independiente y envía via AWS SES o SendGrid con el mensaje: *"Detectamos un nuevo mini-vinilo en tu dispositivo Orpheus. Ingresá a la plataforma cuando quieras para asociarle tu álbum favorito."*

