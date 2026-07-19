from datetime import datetime, timedelta

from app.repositories.user_repository import UserRepository
from app.clients.spotify_client import SpotifyClient
from app.dtos.resource_dto import ResourceListResponse, ResourceResponse

class SpotifyService():
    def __init__(self, user_repository: UserRepository, spotify_client: SpotifyClient):
        self.user_repository = user_repository
        self.spotify_client = spotify_client

    def with_fresh_token(func):
        async def wrapper(self, user, *args, **kwargs):
            now = datetime.utcnow()
            if user.token_expires_at - timedelta(seconds=60) <= now:
                data = await self.spotify_client.exchange_token(user.spotify_refresh_token)
                new_expires_at = datetime.utcnow() + timedelta(seconds=data["expires_in"])
                new_refresh_token = data.get("refresh_token", user.spotify_refresh_token)
                await self.user_repository.update_tokens(
                    user_id=user.id,
                    access_token=data["access_token"],
                    refresh_token=new_refresh_token,
                    token_expires_at=new_expires_at,
                )
                access_token = data["access_token"]
            else:
                access_token = user.spotify_access_token
            return await func(self, access_token, *args, **kwargs)
        return wrapper
    
    #gets the spotify_device_id from the device
    @with_fresh_token
    async def get_spotify_device_id(self, access_token: str, device_name: str) -> str | None:
        devices = await self.spotify_client.get_active_devices(access_token)

        for spotify_device in devices:
            if spotify_device["name"] == device_name:
                return spotify_device["id"]
            
        return None
        
    @with_fresh_token
    async def search(self, access_token: str, query: str, resource_type: str) -> ResourceListResponse:
        raw =  await self.spotify_client.search(access_token,query,resource_type)
        items = []

        for album in raw.get('albums', {}).get("items", {}):
            items.append(ResourceResponse(
                spotify_uri=album["uri"],
                name=album["name"],
                art_url=album["images"][0]["url"] if album.get("images") else None,
                resource_type="album",
                artist=album["artists"][0]["name"] if album.get("artists") else None,
            ))

        for playlist in raw.get("playlists", {}).get("items", []):
            items.append(ResourceResponse(
                spotify_uri=playlist["uri"],
                name=playlist["name"],
                art_url=playlist["images"][0]["url"] if playlist.get("images") else None,
                resource_type="playlist",
                artist=playlist.get("owner", {}).get("display_name"),
            ))

        return ResourceListResponse(items=items,total=len(items))