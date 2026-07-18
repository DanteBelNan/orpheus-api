from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.spotify_service import SpotifyService
from app.exceptions.spotify_exception import SpotifyError


@pytest.fixture
def mock_user_repository():
    repo = MagicMock()
    repo.update_tokens = AsyncMock()
    return repo


@pytest.fixture
def mock_spotify_client():
    client = MagicMock()
    client.exchange_token = AsyncMock()
    client.get_active_devices = AsyncMock()
    client.search = AsyncMock()
    return client


@pytest.fixture
def spotify_service(mock_user_repository, mock_spotify_client):
    return SpotifyService(
        user_repository=mock_user_repository,
        spotify_client=mock_spotify_client,
    )


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


class TestWithFreshTokenDecorator:
    async def test_uses_existing_token_when_fresh(
        self, spotify_service, mock_spotify_client, mock_user_fresh_token
    ):
        mock_spotify_client.get_active_devices.return_value = []

        await spotify_service.get_spotify_device_id(mock_user_fresh_token, "Orpheus #1")

        mock_spotify_client.get_active_devices.assert_called_once_with("valid_access_token")

    async def test_refreshes_token_when_expired(
        self, spotify_service, mock_spotify_client, mock_user_repository, mock_user_expired_token
    ):
        mock_spotify_client.exchange_token.return_value = {
            "access_token": "new_access_token",
            "expires_in": 3600,
        }
        mock_spotify_client.get_active_devices.return_value = []

        await spotify_service.get_spotify_device_id(mock_user_expired_token, "Orpheus #1")

        mock_spotify_client.exchange_token.assert_called_once_with("refresh_token_123")
        mock_spotify_client.get_active_devices.assert_called_once_with("new_access_token")

    async def test_updates_db_after_token_refresh(
        self, spotify_service, mock_spotify_client, mock_user_repository, mock_user_expired_token
    ):
        mock_spotify_client.exchange_token.return_value = {
            "access_token": "new_access_token",
            "expires_in": 3600,
        }
        mock_spotify_client.get_active_devices.return_value = []

        await spotify_service.get_spotify_device_id(mock_user_expired_token, "Orpheus #1")

        mock_user_repository.update_tokens.assert_called_once()

    async def test_does_not_call_exchange_when_token_fresh(
        self, spotify_service, mock_spotify_client, mock_user_fresh_token
    ):
        mock_spotify_client.get_active_devices.return_value = []

        await spotify_service.get_spotify_device_id(mock_user_fresh_token, "Orpheus #1")

        mock_spotify_client.exchange_token.assert_not_called()

    async def test_updates_refresh_token_if_returned(
        self, spotify_service, mock_spotify_client, mock_user_repository, mock_user_expired_token
    ):
        mock_spotify_client.exchange_token.return_value = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_in": 3600,
        }
        mock_spotify_client.get_active_devices.return_value = []

        await spotify_service.get_spotify_device_id(mock_user_expired_token, "Orpheus #1")

        call_kwargs = mock_user_repository.update_tokens.call_args.kwargs
        assert call_kwargs["refresh_token"] == "new_refresh_token"


class TestGetSpotifyDeviceId:
    async def test_returns_device_id_when_name_matches(
        self, spotify_service, mock_spotify_client, mock_user_fresh_token
    ):
        mock_spotify_client.get_active_devices.return_value = [
            {"id": "spotify_abc123", "name": "Orpheus #1"}
        ]

        result = await spotify_service.get_spotify_device_id(mock_user_fresh_token, "Orpheus #1")

        assert result == "spotify_abc123"

    async def test_returns_none_when_device_not_in_list(
        self, spotify_service, mock_spotify_client, mock_user_fresh_token
    ):
        mock_spotify_client.get_active_devices.return_value = [
            {"id": "other_id", "name": "Some Other Speaker"}
        ]

        result = await spotify_service.get_spotify_device_id(mock_user_fresh_token, "Orpheus #1")

        assert result is None

    async def test_returns_none_when_list_empty(
        self, spotify_service, mock_spotify_client, mock_user_fresh_token
    ):
        mock_spotify_client.get_active_devices.return_value = []

        result = await spotify_service.get_spotify_device_id(mock_user_fresh_token, "Orpheus #1")

        assert result is None


class TestSearch:
    async def test_returns_search_results(
        self, spotify_service, mock_spotify_client, mock_user_fresh_token
    ):
        mock_spotify_client.search.return_value = {
            "albums": {"items": [{"name": "Abbey Road", "uri": "spotify:album:xxx"}]}
        }

        result = await spotify_service.search(mock_user_fresh_token, "abbey road", "album")

        assert "albums" in result

    async def test_calls_client_with_correct_params(
        self, spotify_service, mock_spotify_client, mock_user_fresh_token
    ):
        mock_spotify_client.search.return_value = {"albums": {"items": []}}

        await spotify_service.search(mock_user_fresh_token, "abbey road", "album")

        mock_spotify_client.search.assert_called_once_with(
            "valid_access_token", "abbey road", "album"
        )

    async def test_uses_fresh_token_when_expired(
        self, spotify_service, mock_spotify_client, mock_user_repository, mock_user_expired_token
    ):
        mock_spotify_client.exchange_token.return_value = {
            "access_token": "new_access_token",
            "expires_in": 3600,
        }
        mock_spotify_client.search.return_value = {"albums": {"items": []}}

        await spotify_service.search(mock_user_expired_token, "abbey road", "album")

        mock_spotify_client.search.assert_called_once_with(
            "new_access_token", "abbey road", "album"
        )
