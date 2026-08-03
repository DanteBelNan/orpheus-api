import os
import pytest


def _setup_env_vars():
    """Set dummy environment variables before app modules are imported."""
    os.environ.setdefault("SPOTIFY_CLIENT_ID", "test_client_id")
    os.environ.setdefault("SPOTIFY_CLIENT_SECRET", "test_client_secret")
    os.environ.setdefault("SPOTIFY_REDIRECT_URI", "http://localhost:8000/auth/callback")
    os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    os.environ.setdefault("MYSQL_HOST", "localhost")
    os.environ.setdefault("MYSQL_PORT", "3306")
    os.environ.setdefault("MYSQL_USER", "test_user")
    os.environ.setdefault("MYSQL_PASSWORD", "test_password")
    os.environ.setdefault("MYSQL_DATABASE", "test_db")
    os.environ.setdefault("SECRET_KEY", "test_secret_key")


_setup_env_vars()


@pytest.fixture(scope="session", autouse=True)
def setup_env_vars():
    """Keep test env defaults available for tests that mutate env vars."""
    _setup_env_vars()
