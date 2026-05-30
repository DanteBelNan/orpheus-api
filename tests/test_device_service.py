from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.device_service import DeviceService
from app.exceptions.device_exception import DeviceAlreadyRegisteredError, DeviceNotFoundError
from app.exceptions.user_exception import UserNotFoundError


@pytest.fixture
def mock_device_repository():
    repo = MagicMock()
    repo.get_by_user_id = AsyncMock()
    repo.get_by_device_id = AsyncMock()
    repo.insert = AsyncMock()
    repo.update_heartbeat = AsyncMock()
    return repo


@pytest.fixture
def mock_user_repository():
    repo = MagicMock()
    repo.get_by_id = AsyncMock()
    repo.update_tokens = AsyncMock()
    return repo


@pytest.fixture
def device_service(mock_device_repository, mock_user_repository):
    return DeviceService(
        device_repository=mock_device_repository,
        user_repository=mock_user_repository,
    )


@pytest.fixture
def mock_db_user():
    user = MagicMock()
    user.id = 1
    user.spotify_access_token = "valid_access_token"
    user.spotify_refresh_token = "refresh_token_123"
    user.token_expires_at = datetime.utcnow() + timedelta(hours=1)
    return user


@pytest.fixture
def mock_db_device():
    device = MagicMock()
    device.id = 1
    device.device_id = "b8:27:eb:3a:11:cc"
    device.user_id = 1
    device.spotify_device_id = None
    device.name = "Orpheus #1"
    device.last_seen = None
    device.created_at = datetime(2026, 1, 1, 12, 0, 0)
    return device


class TestGetDevicesByUserId:
    async def test_returns_devices_list_response(self, device_service, mock_device_repository, mock_db_device):
        mock_device_repository.get_by_user_id.return_value = [mock_db_device]

        result = await device_service.get_devices_by_user_id(user_id=1)

        assert result.amount == 1
        assert result.devices[0].device_id == "b8:27:eb:3a:11:cc"

    async def test_returns_empty_list_when_no_devices(self, device_service, mock_device_repository):
        mock_device_repository.get_by_user_id.return_value = []

        result = await device_service.get_devices_by_user_id(user_id=1)

        assert result.amount == 0
        assert result.devices == []

    async def test_amount_matches_devices_count(self, device_service, mock_device_repository, mock_db_device):
        second_device = MagicMock()
        second_device.id = 2
        second_device.device_id = "b8:27:eb:3a:22:dd"
        second_device.user_id = 1
        second_device.spotify_device_id = None
        second_device.name = "Orpheus #2"
        second_device.last_seen = None
        second_device.created_at = datetime(2026, 1, 1, 12, 0, 0)

        mock_device_repository.get_by_user_id.return_value = [mock_db_device, second_device]

        result = await device_service.get_devices_by_user_id(user_id=1)

        assert result.amount == 2
        assert len(result.devices) == 2


class TestGetDeviceById:
    async def test_returns_device_response_when_found(self, device_service, mock_device_repository, mock_db_device):
        mock_device_repository.get_by_device_id.return_value = mock_db_device

        result = await device_service.get_device_by_id(device_id="b8:27:eb:3a:11:cc")

        assert result.device_id == "b8:27:eb:3a:11:cc"
        assert result.name == "Orpheus #1"

    async def test_raises_not_found_when_device_missing(self, device_service, mock_device_repository):
        mock_device_repository.get_by_device_id.return_value = None

        with pytest.raises(DeviceNotFoundError):
            await device_service.get_device_by_id(device_id="00:00:00:00:00:00")


class TestCreateDevice:
    async def test_creates_and_returns_device(self, device_service, mock_device_repository, mock_db_device):
        mock_device_repository.get_by_device_id.return_value = None
        mock_device_repository.insert.return_value = mock_db_device

        result = await device_service.create_device(
            device_id="b8:27:eb:3a:11:cc",
            user_id=1,
            name="Orpheus #1",
        )

        assert result.device_id == "b8:27:eb:3a:11:cc"
        assert result.name == "Orpheus #1"

    async def test_calls_insert_with_correct_data(self, device_service, mock_device_repository, mock_db_device):
        mock_device_repository.get_by_device_id.return_value = None
        mock_device_repository.insert.return_value = mock_db_device

        await device_service.create_device(
            device_id="b8:27:eb:3a:11:cc",
            user_id=1,
            name="Orpheus #1",
        )

        mock_device_repository.insert.assert_called_once_with(
            "b8:27:eb:3a:11:cc", 1, "Orpheus #1"
        )

    async def test_raises_already_registered_when_device_exists(self, device_service, mock_device_repository, mock_db_device):
        mock_device_repository.get_by_device_id.return_value = mock_db_device

        with pytest.raises(DeviceAlreadyRegisteredError):
            await device_service.create_device(
                device_id="b8:27:eb:3a:11:cc",
                user_id=1,
                name="Orpheus #1",
            )


class TestEnsureFreshToken:
    async def test_returns_existing_token_when_not_expired(self, device_service, mock_db_user):
        result = await device_service._ensure_fresh_token(mock_db_user)
        assert result == "valid_access_token"

    async def test_refreshes_token_when_expired(self, device_service, mock_user_repository, mock_db_user):
        mock_db_user.token_expires_at = datetime.utcnow() - timedelta(hours=1)

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "access_token": "new_access_token",
            "expires_in": 3600,
        }
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post.return_value = mock_response

        with patch("app.services.device_service.httpx.AsyncClient", return_value=mock_client):
            result = await device_service._ensure_fresh_token(mock_db_user)

        assert result == "new_access_token"
        mock_user_repository.update_tokens.assert_called_once()

    async def test_does_not_call_spotify_when_token_valid(self, device_service, mock_db_user):
        mock_client = AsyncMock()

        with patch("app.services.device_service.httpx.AsyncClient", return_value=mock_client):
            await device_service._ensure_fresh_token(mock_db_user)

        mock_client.__aenter__.assert_not_called()


class TestGetSpotifyDeviceId:
    def _build_mock_client(self, devices: list) -> AsyncMock:
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"devices": devices}
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = mock_response
        return mock_client

    async def test_returns_spotify_device_id_when_name_matches(self, device_service):
        mock_client = self._build_mock_client([
            {"id": "spotify_abc123", "name": "Orpheus #1"},
        ])

        with patch("app.services.device_service.httpx.AsyncClient", return_value=mock_client):
            result = await device_service._get_spotify_device_id("token", "Orpheus #1")

        assert result == "spotify_abc123"

    async def test_returns_none_when_device_not_in_spotify(self, device_service):
        mock_client = self._build_mock_client([
            {"id": "other_id", "name": "Some Other Speaker"},
        ])

        with patch("app.services.device_service.httpx.AsyncClient", return_value=mock_client):
            result = await device_service._get_spotify_device_id("token", "Orpheus #1")

        assert result is None

    async def test_returns_none_when_spotify_returns_empty_list(self, device_service):
        mock_client = self._build_mock_client([])

        with patch("app.services.device_service.httpx.AsyncClient", return_value=mock_client):
            result = await device_service._get_spotify_device_id("token", "Orpheus #1")

        assert result is None


class TestProcessHeartbeat:
    async def test_raises_device_not_found(self, device_service, mock_device_repository):
        mock_device_repository.get_by_device_id.return_value = None

        with pytest.raises(DeviceNotFoundError):
            await device_service.process_heartbeat("00:00:00:00:00:00")

    async def test_raises_user_not_found(self, device_service, mock_device_repository, mock_user_repository, mock_db_device):
        mock_device_repository.get_by_device_id.return_value = mock_db_device
        mock_user_repository.get_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            await device_service.process_heartbeat("b8:27:eb:3a:11:cc")

    async def test_returns_heartbeat_response(self, device_service, mock_device_repository, mock_user_repository, mock_db_device, mock_db_user):
        mock_device_repository.get_by_device_id.return_value = mock_db_device
        mock_user_repository.get_by_id.return_value = mock_db_user

        device_service._ensure_fresh_token = AsyncMock(return_value="valid_token")
        device_service._get_spotify_device_id = AsyncMock(return_value="spotify_abc123")

        result = await device_service.process_heartbeat("b8:27:eb:3a:11:cc")

        assert result.status == "ok"
        assert result.spotify_device_id == "spotify_abc123"

    async def test_updates_heartbeat_in_db(self, device_service, mock_device_repository, mock_user_repository, mock_db_device, mock_db_user):
        mock_device_repository.get_by_device_id.return_value = mock_db_device
        mock_user_repository.get_by_id.return_value = mock_db_user

        device_service._ensure_fresh_token = AsyncMock(return_value="valid_token")
        device_service._get_spotify_device_id = AsyncMock(return_value="spotify_abc123")

        await device_service.process_heartbeat("b8:27:eb:3a:11:cc")

        mock_device_repository.update_heartbeat.assert_called_once_with(
            "b8:27:eb:3a:11:cc", "spotify_abc123"
        )
