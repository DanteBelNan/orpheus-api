from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.clients.spotify_client import SpotifyClient
from app.exceptions.spotify_exception import SpotifyError


@pytest.fixture
def spotify_client():
    return SpotifyClient()


def _build_mock_client(method: str, json_data: dict, status_code: int = 200) -> AsyncMock:
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = json_data
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    setattr(mock_client, method, AsyncMock(return_value=mock_response))
    return mock_client


def _build_error_client(method: str, status_code: int = 401, error_message: str = "Unauthorized") -> AsyncMock:
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.text = error_message
    mock_response.json.return_value = {"error": {"status": status_code, "message": error_message}}
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        str(status_code), request=MagicMock(), response=mock_response
    )
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    setattr(mock_client, method, AsyncMock(return_value=mock_response))
    return mock_client


class TestExchangeToken:
    async def test_returns_token_data(self, spotify_client):
        mock_client = _build_mock_client("post", {
            "access_token": "new_access_token",
            "expires_in": 3600,
        })

        with patch("app.clients.spotify_client.httpx.AsyncClient", return_value=mock_client):
            result = await spotify_client.exchange_token("refresh_token_123")

        assert result["access_token"] == "new_access_token"
        assert result["expires_in"] == 3600

    async def test_sends_refresh_token_in_request(self, spotify_client):
        mock_client = _build_mock_client("post", {
            "access_token": "new_access_token",
            "expires_in": 3600,
        })

        with patch("app.clients.spotify_client.httpx.AsyncClient", return_value=mock_client):
            await spotify_client.exchange_token("my_refresh_token")

        call_data = mock_client.post.call_args.kwargs["data"]
        assert call_data["refresh_token"] == "my_refresh_token"
        assert call_data["grant_type"] == "refresh_token"

    async def test_raises_spotify_error_on_failure(self, spotify_client):
        mock_client = _build_error_client("post", 401, "Invalid token")

        with patch("app.clients.spotify_client.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(SpotifyError) as exc:
                await spotify_client.exchange_token("bad_refresh_token")

        assert "401" in str(exc.value)
        assert "Invalid token" in str(exc.value)


class TestGetActiveDevices:
    async def test_returns_device_list(self, spotify_client):
        mock_client = _build_mock_client("get", {
            "devices": [
                {"id": "abc123", "name": "Orpheus #1", "type": "Speaker"}
            ]
        })

        with patch("app.clients.spotify_client.httpx.AsyncClient", return_value=mock_client):
            result = await spotify_client.get_active_devices("valid_token")

        assert len(result) == 1
        assert result[0]["id"] == "abc123"

    async def test_returns_empty_list_when_no_devices(self, spotify_client):
        mock_client = _build_mock_client("get", {"devices": []})

        with patch("app.clients.spotify_client.httpx.AsyncClient", return_value=mock_client):
            result = await spotify_client.get_active_devices("valid_token")

        assert result == []

    async def test_sends_bearer_token(self, spotify_client):
        mock_client = _build_mock_client("get", {"devices": []})

        with patch("app.clients.spotify_client.httpx.AsyncClient", return_value=mock_client):
            await spotify_client.get_active_devices("my_access_token")

        headers = mock_client.get.call_args.kwargs["headers"]
        assert headers["Authorization"] == "Bearer my_access_token"

    async def test_raises_spotify_error_on_failure(self, spotify_client):
        mock_client = _build_error_client("get", 403, "Insufficient scope")

        with patch("app.clients.spotify_client.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(SpotifyError) as exc:
                await spotify_client.get_active_devices("bad_token")

        assert "403" in str(exc.value)


class TestSearch:
    async def test_returns_raw_spotify_response(self, spotify_client):
        mock_client = _build_mock_client("get", {
            "albums": {"items": [{"name": "Abbey Road", "uri": "spotify:album:xxx"}]}
        })

        with patch("app.clients.spotify_client.httpx.AsyncClient", return_value=mock_client):
            result = await spotify_client.search("valid_token", "abbey road", "album")

        assert "albums" in result

    async def test_sends_correct_query_params(self, spotify_client):
        mock_client = _build_mock_client("get", {"albums": {"items": []}})

        with patch("app.clients.spotify_client.httpx.AsyncClient", return_value=mock_client):
            await spotify_client.search("valid_token", "abbey road", "album,playlist")

        call_params = mock_client.get.call_args.kwargs["params"]
        assert call_params["q"] == "abbey road"
        assert call_params["type"] == "album,playlist"
        assert call_params["limit"] == 10

    async def test_raises_spotify_error_on_failure(self, spotify_client):
        mock_client = _build_error_client("get", 429, "API rate limit exceeded")

        with patch("app.clients.spotify_client.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(SpotifyError) as exc:
                await spotify_client.search("valid_token", "query", "album")

        assert "429" in str(exc.value)
        assert "API rate limit exceeded" in str(exc.value)
