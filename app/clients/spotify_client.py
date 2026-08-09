import httpx
from app.config import settings
from app.exceptions.spotify_exception import SpotifyError

class SpotifyClient():
    def __init__(self):
        pass
    async def exchange_code(self,code: str) -> dict:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    settings.spotify_token_url,
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": settings.spotify_redirect_uri,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    auth=(settings.spotify_client_id, settings.spotify_client_secret),
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json().get("error", {}).get("message", e.response.text)
            except Exception:
                detail = e.response.text
            raise SpotifyError(f"[Spotify API] failed to exchange code ({e.response.status_code}): {detail}")
        
    async def get_user_profile(self, access_token: str) -> dict:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.spotify_api_url}/v1/me",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError:
            raise SpotifyError("Failed to retrieve user profile")

    async def exchange_token(self, refresh_token: str) -> dict:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    settings.spotify_token_url,
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
                    f"{settings.spotify_api_url}/v1/me/player/devices",
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
    async def search(self, access_token: str, query: str, resource_type: str, limit: int = 10) -> dict:
        try:
            async with httpx.AsyncClient() as client:
                url = f"{settings.spotify_api_url.rstrip('/')}/v1/search"
                response = await client.get(
                    url,
                    params={"q": query, "type": resource_type, "limit": limit},
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
        
    async def play(self, access_token: str, device_id: str, spotify_uri: str, song_index: int = 0, ms_delay: int = 0) -> None:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{settings.spotify_api_url}/v1/me/player/play",
                    headers={"Authorization": f"Bearer {access_token}"},
                    params={"device_id": device_id},
                    json={
                        "context_uri": spotify_uri,
                        "offset": {
                            "position": song_index,
                        },
                        "position_ms": ms_delay
                    }
                )
                response.raise_for_status()
                return
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json().get("error", {}).get("message", e.response.text)
            except Exception:
                detail = e.response.text
            raise SpotifyError(f"[Spotify API] failed to play resource ({e.response.status_code}): {detail}")     

    async def state(self, access_token: str) -> dict:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.spotify_api_url}/v1/me/player",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                if response.status_code == 204:
                    return {}
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json().get("error", {}).get("message", e.response.text)
            except Exception:
                detail = e.response.text
            raise SpotifyError(f"[Spotify API] failed to get state of resource ({e.response.status_code}): {detail}")  

