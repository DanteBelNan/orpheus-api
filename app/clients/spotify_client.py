import httpx
from app.config import settings
from app.exceptions.spotify_exception import SpotifyError

class SpotifyClient():
    def __init__(self):
        pass

    async def exchange_token(self, refresh_token: str) -> dict:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://accounts.spotify.com/api/token",
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    auth=(settings.spotify_client_id, settings.spotify_client_secret),
                )
                response.raise_for_status()
                data = response.json()
                return data
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json().get("error", {}).get("message", e.response.text)
            except Exception:
                detail = e.response.text
            raise SpotifyError(f"[Spotify API] failed to exchange token ({e.response.status_code}): {detail}")

    async def get_active_devices(self, access_token: str) -> list:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.spotify.com/v1/me/player/devices",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                response.raise_for_status()
                data = response.json()
                return data.get("devices", [])
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json().get("error", {}).get("message", e.response.text)
            except Exception:
                detail = e.response.text
            raise SpotifyError(f"[Spotify API] failed to get devices ({e.response.status_code}): {detail}")
        
    async def search(self, access_token: str, query: str, resource_type: str) -> dict:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.spotify.com/v1/search",
                    params={"q": query,"type": resource_type, "limit": 20},
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json().get("error", {}).get("message", e.response.text)
            except Exception:
                detail = e.response.text
            raise SpotifyError(f"[Spotify API] failed to search ({e.response.status_code}): {detail}")

