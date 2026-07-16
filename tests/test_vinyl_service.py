from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

import pytest

from app.services.vinyl_service import VinylService
from app.exceptions.vinyl_exception import VinylNotFoundError


@pytest.fixture
def mock_vinyl_repository():
    repo = MagicMock()
    repo.get_all = AsyncMock()
    repo.get_by_id = AsyncMock()
    return repo


@pytest.fixture
def vinyl_service(mock_vinyl_repository):
    return VinylService(vinyl_repository=mock_vinyl_repository)


@pytest.fixture
def mock_db_vinyl():
    vinyl = MagicMock()
    vinyl.id = 1
    vinyl.tag_id = "04:A2:B3:C4"
    vinyl.created_by = 1
    vinyl.name = "Road Trips"
    vinyl.spotify_uri = "spotify:album:xxx"
    vinyl.album_name = "Abbey Road"
    vinyl.album_art_url = "https://example.com/art.jpg"
    vinyl.last_played = None
    vinyl.created_at = datetime(2026, 1, 1, 12, 0, 0)
    return vinyl


@pytest.fixture
def mock_db_vinyl_pending():
    vinyl = MagicMock()
    vinyl.id = 2
    vinyl.tag_id = "04:FF:BB:CC"
    vinyl.created_by = 1
    vinyl.name = None
    vinyl.spotify_uri = None
    vinyl.album_name = None
    vinyl.album_art_url = None
    vinyl.last_played = None
    vinyl.created_at = datetime(2026, 1, 1, 12, 0, 0)
    return vinyl


class TestGetAllVinyls:
    async def test_returns_vinyl_list_response(self, vinyl_service, mock_vinyl_repository, mock_db_vinyl):
        mock_vinyl_repository.get_all.return_value = [mock_db_vinyl]

        result = await vinyl_service.get_all_vinyls(page=1, take=50)

        assert result.amount == 1
        assert result.vinyls[0].tag_id == "04:A2:B3:C4"

    async def test_returns_empty_list_when_no_vinyls(self, vinyl_service, mock_vinyl_repository):
        mock_vinyl_repository.get_all.return_value = []

        result = await vinyl_service.get_all_vinyls(page=1, take=50)

        assert result.amount == 0
        assert result.vinyls == []

    async def test_calculates_skip_correctly(self, vinyl_service, mock_vinyl_repository):
        mock_vinyl_repository.get_all.return_value = []

        await vinyl_service.get_all_vinyls(page=3, take=10)

        mock_vinyl_repository.get_all.assert_called_once_with(None, None, 20, 10)

    async def test_passes_filters_to_repository(self, vinyl_service, mock_vinyl_repository):
        mock_vinyl_repository.get_all.return_value = []

        await vinyl_service.get_all_vinyls(page=1, take=50, created_by=5, status="pending")

        mock_vinyl_repository.get_all.assert_called_once_with(5, "pending", 0, 50)

    async def test_status_is_configured_when_spotify_uri_set(self, vinyl_service, mock_vinyl_repository, mock_db_vinyl):
        mock_vinyl_repository.get_all.return_value = [mock_db_vinyl]

        result = await vinyl_service.get_all_vinyls(page=1, take=50)

        assert result.vinyls[0].status == "configured"

    async def test_status_is_pending_when_spotify_uri_null(self, vinyl_service, mock_vinyl_repository, mock_db_vinyl_pending):
        mock_vinyl_repository.get_all.return_value = [mock_db_vinyl_pending]

        result = await vinyl_service.get_all_vinyls(page=1, take=50)

        assert result.vinyls[0].status == "pending"


class TestGetVinylById:
    async def test_returns_vinyl_response_when_found(self, vinyl_service, mock_vinyl_repository, mock_db_vinyl):
        mock_vinyl_repository.get_by_id.return_value = mock_db_vinyl

        result = await vinyl_service.get_vinyl_by_id(1)

        assert result.id == 1
        assert result.tag_id == "04:A2:B3:C4"

    async def test_raises_not_found_when_vinyl_missing(self, vinyl_service, mock_vinyl_repository):
        mock_vinyl_repository.get_by_id.return_value = None

        with pytest.raises(VinylNotFoundError):
            await vinyl_service.get_vinyl_by_id(99)

    async def test_status_computed_correctly(self, vinyl_service, mock_vinyl_repository, mock_db_vinyl):
        mock_vinyl_repository.get_by_id.return_value = mock_db_vinyl

        result = await vinyl_service.get_vinyl_by_id(1)

        assert result.status == "configured"
