from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.play_service import PlayService
from app.exceptions.base_exception import ExternalServiceError
from app.exceptions.device_exception import DeviceNotFoundError
from app.exceptions.user_exception import UserNotFoundError
from app.exceptions.vinyl_exception import VinylCreated, VinylPending


@pytest.fixture
def mock_vinyl_repository():
    repo = MagicMock()
    repo.get_by_tag_id = AsyncMock()
    repo.create = AsyncMock()
    return repo


@pytest.fixture
def mock_spotify_service():
    service = MagicMock()
    service.play = AsyncMock()
    return service


@pytest.fixture
def mock_user_repository():
    repo = MagicMock()
    repo.get_by_id = AsyncMock()
    return repo


@pytest.fixture
def mock_device_repository():
    repo = MagicMock()
    repo.get_by_device_id = AsyncMock()
    return repo


@pytest.fixture
def play_service(
    mock_vinyl_repository,
    mock_spotify_service,
    mock_user_repository,
    mock_device_repository,
):
    return PlayService(
        vinyl_repository=mock_vinyl_repository,
        spotify_service=mock_spotify_service,
        user_repository=mock_user_repository,
        device_repository=mock_device_repository,
    )


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = 1
    user.spotify_access_token = "valid_token"
    return user


@pytest.fixture
def mock_device():
    device = MagicMock()
    device.device_id = "b8:27:eb:xx"
    device.user_id = 1
    device.spotify_device_id = "spotify_abc123"
    return device


@pytest.fixture
def mock_vinyl_configured():
    vinyl = MagicMock()
    vinyl.id = 7
    vinyl.tag_id = "04:A2:B3:C4"
    vinyl.spotify_uri = "spotify:album:xxx"
    vinyl.created_by = 1
    return vinyl


@pytest.fixture
def mock_vinyl_pending():
    vinyl = MagicMock()
    vinyl.id = 8
    vinyl.tag_id = "04:FF:BB:CC"
    vinyl.spotify_uri = None
    vinyl.created_by = 1
    return vinyl


class TestPlayRegistersNewTag:
    async def test_creates_vinyl_when_tag_unknown(
        self,
        play_service,
        mock_vinyl_repository,
        mock_user_repository,
        mock_device_repository,
        mock_user,
        mock_device,
    ):
        mock_device_repository.get_by_device_id.return_value = mock_device
        mock_user_repository.get_by_id.return_value = mock_user
        mock_vinyl_repository.get_by_tag_id.return_value = None
        new_vinyl = MagicMock()
        new_vinyl.id = 9
        mock_vinyl_repository.create.return_value = new_vinyl

        with pytest.raises(VinylCreated):
            await play_service.play("b8:27:eb:xx", "04:NEW:TAG")

    async def test_calls_create_with_correct_args(
        self,
        play_service,
        mock_vinyl_repository,
        mock_user_repository,
        mock_device_repository,
        mock_user,
        mock_device,
    ):
        mock_device_repository.get_by_device_id.return_value = mock_device
        mock_user_repository.get_by_id.return_value = mock_user
        mock_vinyl_repository.get_by_tag_id.return_value = None
        new_vinyl = MagicMock()
        new_vinyl.id = 9
        mock_vinyl_repository.create.return_value = new_vinyl

        with pytest.raises(VinylCreated):
            await play_service.play("b8:27:eb:xx", "04:NEW:TAG")

        mock_vinyl_repository.create.assert_called_once_with("04:NEW:TAG", mock_user.id)

    async def test_raised_vinyl_created_contains_vinyl_id(
        self,
        play_service,
        mock_vinyl_repository,
        mock_user_repository,
        mock_device_repository,
        mock_user,
        mock_device,
    ):
        mock_device_repository.get_by_device_id.return_value = mock_device
        mock_user_repository.get_by_id.return_value = mock_user
        mock_vinyl_repository.get_by_tag_id.return_value = None
        new_vinyl = MagicMock()
        new_vinyl.id = 9
        mock_vinyl_repository.create.return_value = new_vinyl

        with pytest.raises(VinylCreated) as exc:
            await play_service.play("b8:27:eb:xx", "04:NEW:TAG")

        assert "9" in str(exc.value)

    async def test_does_not_call_spotify_when_new_tag(
        self,
        play_service,
        mock_vinyl_repository,
        mock_spotify_service,
        mock_user_repository,
        mock_device_repository,
        mock_user,
        mock_device,
    ):
        mock_device_repository.get_by_device_id.return_value = mock_device
        mock_user_repository.get_by_id.return_value = mock_user
        mock_vinyl_repository.get_by_tag_id.return_value = None
        mock_vinyl_repository.create.return_value = MagicMock(id=9)

        with pytest.raises(VinylCreated):
            await play_service.play("b8:27:eb:xx", "04:NEW:TAG")

        mock_spotify_service.play.assert_not_called()


class TestPlayPendingVinyl:
    async def test_raises_vinyl_pending_when_no_spotify_uri(
        self,
        play_service,
        mock_vinyl_repository,
        mock_user_repository,
        mock_device_repository,
        mock_user,
        mock_device,
        mock_vinyl_pending,
    ):
        mock_device_repository.get_by_device_id.return_value = mock_device
        mock_user_repository.get_by_id.return_value = mock_user
        mock_vinyl_repository.get_by_tag_id.return_value = mock_vinyl_pending

        with pytest.raises(VinylPending):
            await play_service.play("b8:27:eb:xx", "04:FF:BB:CC")

    async def test_does_not_call_spotify_when_pending(
        self,
        play_service,
        mock_vinyl_repository,
        mock_spotify_service,
        mock_user_repository,
        mock_device_repository,
        mock_user,
        mock_device,
        mock_vinyl_pending,
    ):
        mock_device_repository.get_by_device_id.return_value = mock_device
        mock_user_repository.get_by_id.return_value = mock_user
        mock_vinyl_repository.get_by_tag_id.return_value = mock_vinyl_pending

        with pytest.raises(VinylPending):
            await play_service.play("b8:27:eb:xx", "04:FF:BB:CC")

        mock_spotify_service.play.assert_not_called()


class TestPlayConfiguredVinyl:
    async def test_calls_spotify_with_correct_args(
        self,
        play_service,
        mock_vinyl_repository,
        mock_spotify_service,
        mock_user_repository,
        mock_device_repository,
        mock_user,
        mock_device,
        mock_vinyl_configured,
    ):
        mock_device_repository.get_by_device_id.return_value = mock_device
        mock_user_repository.get_by_id.return_value = mock_user
        mock_vinyl_repository.get_by_tag_id.return_value = mock_vinyl_configured

        await play_service.play("b8:27:eb:xx", "04:A2:B3:C4")

        mock_spotify_service.play.assert_called_once_with(
            mock_user, "spotify_abc123", "spotify:album:xxx", 0, 0
        )

    async def test_passes_song_index_and_delay(
        self,
        play_service,
        mock_vinyl_repository,
        mock_spotify_service,
        mock_user_repository,
        mock_device_repository,
        mock_user,
        mock_device,
        mock_vinyl_configured,
    ):
        mock_device_repository.get_by_device_id.return_value = mock_device
        mock_user_repository.get_by_id.return_value = mock_user
        mock_vinyl_repository.get_by_tag_id.return_value = mock_vinyl_configured

        await play_service.play("b8:27:eb:xx", "04:A2:B3:C4", song_index=3, ms_delay=12000)

        mock_spotify_service.play.assert_called_once_with(
            mock_user, "spotify_abc123", "spotify:album:xxx", 3, 12000
        )

    async def test_does_not_raise_for_configured_vinyl(
        self,
        play_service,
        mock_vinyl_repository,
        mock_spotify_service,
        mock_user_repository,
        mock_device_repository,
        mock_user,
        mock_device,
        mock_vinyl_configured,
    ):
        mock_device_repository.get_by_device_id.return_value = mock_device
        mock_user_repository.get_by_id.return_value = mock_user
        mock_vinyl_repository.get_by_tag_id.return_value = mock_vinyl_configured

        try:
            await play_service.play("b8:27:eb:xx", "04:A2:B3:C4")
        except (VinylCreated, VinylPending):
            pytest.fail("Should not raise VinylCreated or VinylPending for configured vinyl")


class TestPlayDeviceAndUserLookup:
    async def test_raises_device_not_found_when_device_missing(
        self, play_service, mock_device_repository
    ):
        mock_device_repository.get_by_device_id.return_value = None

        with pytest.raises(DeviceNotFoundError):
            await play_service.play("unknown-device", "04:A2:B3:C4")

    async def test_raises_external_service_error_when_spotify_device_missing(
        self, play_service, mock_device_repository, mock_device
    ):
        mock_device.spotify_device_id = None
        mock_device_repository.get_by_device_id.return_value = mock_device

        with pytest.raises(ExternalServiceError):
            await play_service.play("b8:27:eb:xx", "04:A2:B3:C4")

    async def test_raises_user_not_found_when_owner_missing(
        self,
        play_service,
        mock_user_repository,
        mock_device_repository,
        mock_device,
    ):
        mock_device_repository.get_by_device_id.return_value = mock_device
        mock_user_repository.get_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            await play_service.play("b8:27:eb:xx", "04:A2:B3:C4")
