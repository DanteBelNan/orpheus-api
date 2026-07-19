CREATE TABLE IF NOT EXISTS users (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    email           VARCHAR(255) NOT NULL UNIQUE,
    spotify_user_id VARCHAR(255) NOT NULL UNIQUE,
    spotify_refresh_token TEXT NOT NULL,
    spotify_access_token  TEXT NOT NULL,
    token_expires_at      DATETIME NOT NULL,
    created_at            DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS devices (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    device_id         VARCHAR(255) NOT NULL UNIQUE,
    user_id           INT NOT NULL,
    spotify_device_id VARCHAR(255),
    name              VARCHAR(255) NOT NULL,
    last_seen         DATETIME,
    created_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS vinyls (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    tag_id        VARCHAR(255) NOT NULL UNIQUE,
    created_by    INT NOT NULL,
    name          VARCHAR(255),
    spotify_uri   VARCHAR(255),
    album_name    VARCHAR(255),
    album_art_url TEXT,
    last_played   DATETIME,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
);
