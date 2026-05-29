from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.device_service import DeviceService
from app.exceptions.device_exception import DeviceAlreadyRegisteredError, DeviceNotFoundError


@pytest.fixture
def mock_device_repository():
    repo = MagicMock()
    repo.get_by_user_id = AsyncMock()
    repo.get_by_device_id = AsyncMock()
    repo.insert = AsyncMock()
    return repo


@pytest.fixture
def device_service(mock_device_repository):
    return DeviceService(device_repository=mock_device_repository)


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
