from datetime import datetime, timedelta

from app.repositories.user_repository import UserRepository
from app.clients.spotify_client import SpotifyClient
from app.dtos.resource_dto import ResourceListResponse, ResourceResponse
from app.logger import get_logger
from app.dtos.play_dto import StateResponse

logger = get_logger(__name__)

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
                logger.info("Spotify token refreshed", extra={"user_id": user.id})
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

        albums_data = raw.get('albums') or {}
        for album in albums_data.get("items") or []:
            if not album:
                continue
            images = album.get("images") or []
            artists = album.get("artists") or []
            items.append(ResourceResponse(
                spotify_uri=album.get("uri", ""),
                name=album.get("name", ""),
                art_url=images[0]["url"] if images else None,
                resource_type="album",
                artist=artists[0]["name"] if artists else None,
            ))

        playlists_data = raw.get("playlists") or {}
        for playlist in playlists_data.get("items") or []:
            if not playlist:
                continue
            images = playlist.get("images") or []
            owner = playlist.get("owner") or {}
            items.append(ResourceResponse(
                spotify_uri=playlist.get("uri", ""),
                name=playlist.get("name", ""),
                art_url=images[0]["url"] if images else None,
                resource_type="playlist",
                artist=owner.get("display_name"),
            ))

        return ResourceListResponse(items=items,total=len(items))

    
    @with_fresh_token
    async def play(self, access_token: str, device_id: str, spotify_uri: str, song_index: int = 0, ms_delay: int = 0):    
        return await self.spotify_client.play(access_token,device_id,spotify_uri,song_index,ms_delay)
    
    @with_fresh_token
    async def state(self, access_token: str) -> StateResponse: 
        raw_state = await self.spotify_client.state(access_token)

        item = raw_state.get("item", {})

        spotify_state = StateResponse(
            is_playing = raw_state.get("is_playing", False),
            track_name=item.get("name", "Desconocido"),
            album_name=item.get("album", {}).get("name", "Desconocido"),
            # Spotify devuelve una lista de artistas, unimos sus nombres con comas
            artist_name=", ".join([artist["name"] for artist in item.get("artists", [])]) or "Desconocido",
            total_tracks=item.get("album", {}).get("total_tracks", 0),
            current_track=item.get("track_number", 0),
            # Extraemos la URL de la primera imagen del álbum (suele ser la de mayor resolución)
            image_url=item.get("album", {}).get("images", [{}])[0].get("url", ""),
            duration=item.get("duration_ms", 0),
            progress=raw_state.get("progress_ms", 0)
        )

        return spotify_state

    