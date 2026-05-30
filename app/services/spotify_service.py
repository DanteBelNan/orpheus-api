import httpx
from datetime import datetime, timedelta

from app.exceptions.spotify_exception import SpotifyError
from app.config import settings

class SpotifyService():
    def __init__(self, user_repository):
        self.user_repository = user_repository

    #checks if the token of the user is fresh, if not, refreshes it with the db
    async def ensure_fresh_token(self, user) -> str: #this may need to be a dependencie in all the endpoints that connects with raspberry
        try:
            now = datetime.utcnow()
            if user.token_expires_at - timedelta(seconds=60) <= now:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        "https://accounts.spotify.com/api/token",
                        data={
                            "grant_type": "refresh_token",
                            "refresh_token": user.spotify_refresh_token,
                        },
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                        auth=(settings.spotify_client_id, settings.spotify_client_secret),
                    )
                    response.raise_for_status()
                    data = response.json()
                new_expires_at = datetime.utcnow() + timedelta(seconds=data["expires_in"])
                await self.user_repository.update_tokens(
                    user_id=user.id,
                    access_token=data["access_token"],
                    token_expires_at=new_expires_at,
                )
                return data["access_token"]
            return user.spotify_access_token
        except httpx.HTTPStatusError:
            raise SpotifyError("Failed to refresh access token")
    
    #gets the spotify_device_id from the device
    async def  get_spotify_device_id(self, access_token: str, device_name: str) -> str | None:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.spotify.com/v1/me/player/devices",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                response.raise_for_status()
                data = response.json()

            for spotify_device in data.get("devices", []):
                if spotify_device["name"] == device_name:
                    return spotify_device["id"]
                
            return None
        except httpx.HTTPStatusError:
            raise SpotifyError("Failed to get spotify device id")