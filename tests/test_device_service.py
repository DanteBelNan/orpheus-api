from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.device_service import DeviceService
from app.exceptions.device_exception import (
    DeviceAlreadyRegisteredError,
    DeviceForbiddenError,
    DeviceNotFoundError,
)
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
def mock_spotify_service():
    service = MagicMock()
    service.ensure_fresh_token = AsyncMock()
    service.get_spotify_device_id = AsyncMock()
    return service


@pytest.fixture
def device_service(mock_device_repository, mock_user_repository, mock_spotify_service):
    return DeviceService(
        device_repository=mock_device_repository,
        user_repository=mock_user_repository,
        spotify_service=mock_spotify_service,
    )


@pytest.fixture
def mock_db_user():
    user = MagicMock()
    user.id = 1
    user.spotify_access_token = "valid_access_token"
    user.spotify_refresh_token = "refresh_token_123"
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

        result = await device_service.get_device_by_id(
            device_id="b8:27:eb:3a:11:cc",
            user_id=1,
        )

        assert result.device_id == "b8:27:eb:3a:11:cc"
        assert result.name == "Orpheus #1"

    async def test_raises_not_found_when_device_missing(self, device_service, mock_device_repository):
        mock_device_repository.get_by_device_id.return_value = None

        with pytest.raises(DeviceNotFoundError):
            await device_service.get_device_by_id(
                device_id="00:00:00:00:00:00",
                user_id=1,
            )

    async def test_raises_forbidden_when_device_belongs_to_other_user(
        self, device_service, mock_device_repository, mock_db_device
    ):
        mock_db_device.user_id = 2
        mock_device_repository.get_by_device_id.return_value = mock_db_device

        with pytest.raises(DeviceForbiddenError):
            await device_service.get_device_by_id(
                device_id="b8:27:eb:3a:11:cc",
                user_id=1,
            )


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

    async def test_returns_heartbeat_response(self, device_service, mock_device_repository, mock_user_repository, mock_spotify_service, mock_db_device, mock_db_user):
        mock_device_repository.get_by_device_id.return_value = mock_db_device
        mock_user_repository.get_by_id.return_value = mock_db_user
        mock_spotify_service.ensure_fresh_token.return_value = "valid_token"
        mock_spotify_service.get_spotify_device_id.return_value = "spotify_abc123"

        result = await device_service.process_heartbeat("b8:27:eb:3a:11:cc")

        assert result.status == "ok"
        assert result.spotify_device_id == "spotify_abc123"

    async def test_updates_heartbeat_in_db(self, device_service, mock_device_repository, mock_user_repository, mock_spotify_service, mock_db_device, mock_db_user):
        mock_device_repository.get_by_device_id.return_value = mock_db_device
        mock_user_repository.get_by_id.return_value = mock_db_user
        mock_spotify_service.ensure_fresh_token.return_value = "valid_token"
        mock_spotify_service.get_spotify_device_id.return_value = "spotify_abc123"

        await device_service.process_heartbeat("b8:27:eb:3a:11:cc")

        mock_device_repository.update_heartbeat.assert_called_once_with(
            "b8:27:eb:3a:11:cc", "spotify_abc123"
        )
