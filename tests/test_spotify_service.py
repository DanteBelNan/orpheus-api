from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.spotify_service import SpotifyService
from app.exceptions.spotify_exception import SpotifyError


@pytest.fixture
def mock_user_repository():
    repo = MagicMock()
    repo.update_tokens = AsyncMock()
    return repo


@pytest.fixture
def spotify_service(mock_user_repository):
    return SpotifyService(user_repository=mock_user_repository)


@pytest.fixture
def mock_user_fresh_token():
    user = MagicMock()
    user.id = 1
    user.spotify_access_token = "valid_access_token"
    user.spotify_refresh_token = "refresh_token_123"
    user.token_expires_at = datetime.utcnow() + timedelta(hours=1)
    return user


@pytest.fixture
def mock_user_expired_token():
    user = MagicMock()
    user.id = 1
    user.spotify_access_token = "expired_access_token"
    user.spotify_refresh_token = "refresh_token_123"
    user.token_expires_at = datetime.utcnow() - timedelta(hours=1)
    return user


def _build_mock_http_client(method: str, json_data: dict) -> AsyncMock:
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = json_data
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    setattr(mock_client, method, AsyncMock(return_value=mock_response))
    return mock_client


class TestEnsureFreshToken:
    async def test_returns_existing_token_when_not_expired(self, spotify_service, mock_user_fresh_token):
        result = await spotify_service.ensure_fresh_token(mock_user_fresh_token)
        assert result == "valid_access_token"

    async def test_does_not_call_spotify_when_token_valid(self, spotify_service, mock_user_fresh_token):
        mock_client = AsyncMock()

        with patch("app.services.spotify_service.httpx.AsyncClient", return_value=mock_client):
            await spotify_service.ensure_fresh_token(mock_user_fresh_token)

        mock_client.__aenter__.assert_not_called()

    async def test_refreshes_token_when_expired(self, spotify_service, mock_user_repository, mock_user_expired_token):
        mock_client = _build_mock_http_client("post", {
            "access_token": "new_access_token",
            "expires_in": 3600,
        })

        with patch("app.services.spotify_service.httpx.AsyncClient", return_value=mock_client):
            result = await spotify_service.ensure_fresh_token(mock_user_expired_token)

        assert result == "new_access_token"

    async def test_updates_tokens_in_db_after_refresh(self, spotify_service, mock_user_repository, mock_user_expired_token):
        mock_client = _build_mock_http_client("post", {
            "access_token": "new_access_token",
            "expires_in": 3600,
        })

        with patch("app.services.spotify_service.httpx.AsyncClient", return_value=mock_client):
            await spotify_service.ensure_fresh_token(mock_user_expired_token)

        mock_user_repository.update_tokens.assert_called_once()

    async def test_raises_spotify_error_when_refresh_fails(self, spotify_service, mock_user_expired_token):
        import httpx
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "401", request=MagicMock(), response=MagicMock()
        )
        mock_client.post.return_value = mock_response

        with patch("app.services.spotify_service.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(SpotifyError):
                await spotify_service.ensure_fresh_token(mock_user_expired_token)


class TestGetSpotifyDeviceId:
    async def test_returns_device_id_when_name_matches(self, spotify_service):
        mock_client = _build_mock_http_client("get", {
            "devices": [{"id": "spotify_abc123", "name": "Orpheus #1"}]
        })

        with patch("app.services.spotify_service.httpx.AsyncClient", return_value=mock_client):
            result = await spotify_service.get_spotify_device_id("token", "Orpheus #1")

        assert result == "spotify_abc123"

    async def test_returns_none_when_device_not_in_list(self, spotify_service):
        mock_client = _build_mock_http_client("get", {
            "devices": [{"id": "other_id", "name": "Some Other Speaker"}]
        })

        with patch("app.services.spotify_service.httpx.AsyncClient", return_value=mock_client):
            result = await spotify_service.get_spotify_device_id("token", "Orpheus #1")

        assert result is None

    async def test_returns_none_when_spotify_returns_empty_list(self, spotify_service):
        mock_client = _build_mock_http_client("get", {"devices": []})

        with patch("app.services.spotify_service.httpx.AsyncClient", return_value=mock_client):
            result = await spotify_service.get_spotify_device_id("token", "Orpheus #1")

        assert result is None

    async def test_raises_spotify_error_when_api_fails(self, spotify_service):
        import httpx
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "401", request=MagicMock(), response=MagicMock()
        )
        mock_client.get.return_value = mock_response

        with patch("app.services.spotify_service.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(SpotifyError):
                await spotify_service.get_spotify_device_id("token", "Orpheus #1")
