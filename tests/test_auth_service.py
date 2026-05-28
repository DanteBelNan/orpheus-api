from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch, ANY

import pytest
from jose import jwt

from app.config import settings
from app.dtos.user_dto import SpotifyTokenData, SpotifyUserData
from app.services.auth_service import AuthService


@pytest.fixture
def mock_user_repository():
    repo = MagicMock()
    repo.upsert = AsyncMock()
    return repo


@pytest.fixture
def auth_service(mock_user_repository):
    return AuthService(user_repository=mock_user_repository)


@pytest.fixture
def mock_db_user():
    user = MagicMock()
    user.id = 1
    user.email = "user@example.com"
    user.spotify_user_id = "spotify_123"
    user.created_at = datetime(2026, 1, 1, 12, 0, 0)
    return user


class TestGetLoginUrl:
    def test_contains_spotify_auth_url(self, auth_service):
        url = auth_service.get_login_url()
        assert "accounts.spotify.com/authorize" in url

    def test_contains_client_id(self, auth_service):
        url = auth_service.get_login_url()
        assert settings.spotify_client_id in url

    def test_contains_required_scopes(self, auth_service):
        url = auth_service.get_login_url()
        assert "user-read-email" in url
        assert "streaming" in url

    def test_contains_redirect_uri(self, auth_service):
        url = auth_service.get_login_url()
        assert "redirect_uri" in url


class TestExchangeCode:
    def _build_mock_client(self, json_data: dict) -> AsyncMock:
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = json_data

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post.return_value = mock_response
        return mock_client

    async def test_returns_spotify_token_data(self, auth_service):
        mock_client = self._build_mock_client({
            "access_token": "access_123",
            "refresh_token": "refresh_456",
            "expires_in": 3600,
        })

        with patch("app.services.auth_service.httpx.AsyncClient", return_value=mock_client):
            result = await auth_service.exchange_code("auth_code_123")

        assert result.access_token == "access_123"
        assert result.refresh_token == "refresh_456"
        assert result.expires_in == 3600

    async def test_sends_correct_code_to_spotify(self, auth_service):
        mock_client = self._build_mock_client({
            "access_token": "access_123",
            "refresh_token": "refresh_456",
            "expires_in": 3600,
        })

        with patch("app.services.auth_service.httpx.AsyncClient", return_value=mock_client):
            await auth_service.exchange_code("my_code_xyz")

        call_data = mock_client.post.call_args.kwargs["data"]
        assert call_data["code"] == "my_code_xyz"
        assert call_data["grant_type"] == "authorization_code"


class TestGetSpotifyUser:
    def _build_mock_client(self, json_data: dict) -> AsyncMock:
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = json_data

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = mock_response
        return mock_client

    async def test_returns_spotify_user_data(self, auth_service):
        mock_client = self._build_mock_client({
            "id": "spotify_user_123",
            "email": "user@example.com",
        })

        with patch("app.services.auth_service.httpx.AsyncClient", return_value=mock_client):
            result = await auth_service.get_spotify_user("access_token_123")

        assert result.spotify_user_id == "spotify_user_123"
        assert result.email == "user@example.com"

    async def test_sends_bearer_authorization_header(self, auth_service):
        mock_client = self._build_mock_client({
            "id": "spotify_user_123",
            "email": "user@example.com",
        })

        with patch("app.services.auth_service.httpx.AsyncClient", return_value=mock_client):
            await auth_service.get_spotify_user("my_access_token")

        headers = mock_client.get.call_args.kwargs["headers"]
        assert headers["Authorization"] == "Bearer my_access_token"


class TestHandleCallback:
    async def test_returns_jwt_and_user_response(
        self, auth_service, mock_user_repository, mock_db_user
    ):
        auth_service.exchange_code = AsyncMock(return_value=SpotifyTokenData(
            access_token="access_123",
            refresh_token="refresh_456",
            expires_in=3600,
        ))
        auth_service.get_spotify_user = AsyncMock(return_value=SpotifyUserData(
            spotify_user_id="spotify_123",
            email="user@example.com",
        ))
        mock_user_repository.upsert.return_value = mock_db_user

        jwt_token, user_response = await auth_service.handle_callback("auth_code")

        assert jwt_token is not None
        assert user_response.email == "user@example.com"
        assert user_response.id == 1

    async def test_calls_upsert_with_correct_data(
        self, auth_service, mock_user_repository, mock_db_user
    ):
        auth_service.exchange_code = AsyncMock(return_value=SpotifyTokenData(
            access_token="access_123",
            refresh_token="refresh_456",
            expires_in=3600,
        ))
        auth_service.get_spotify_user = AsyncMock(return_value=SpotifyUserData(
            spotify_user_id="spotify_123",
            email="user@example.com",
        ))
        mock_user_repository.upsert.return_value = mock_db_user

        await auth_service.handle_callback("auth_code")

        mock_user_repository.upsert.assert_called_once_with(
            spotify_user_id="spotify_123",
            email="user@example.com",
            access_token="access_123",
            refresh_token="refresh_456",
            token_expires_at=ANY,
        )


class TestCreateJwt:
    def test_jwt_contains_correct_user_id(self, auth_service):
        token = auth_service._create_jwt(42)
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        assert payload["sub"] == "42"

    def test_jwt_expiry_matches_config(self, auth_service):
        token = auth_service._create_jwt(1)
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        expected_exp = datetime.utcnow() + timedelta(hours=settings.jwt_expire_hours)
        actual_exp = datetime.utcfromtimestamp(payload["exp"])
        assert abs((actual_exp - expected_exp).total_seconds()) < 5
