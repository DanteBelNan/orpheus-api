from app.repositories.vinyl_repository import VinylRepository
from app.repositories.user_repository import UserRepository
from app.services.spotify_service import SpotifyService
from app.models.user import User
from app.exceptions.vinyl_exception import VinylPending, VinylCreated

class PlayService:
    def __init__(
            self, 
            vinyl_repository: VinylRepository, 
            spotify_service: SpotifyService,
        ):
        self.vinyl_repository = vinyl_repository
        self.spotify_service = spotify_service

    async def play(self, user: User, device_id: str, tag_id: str, song_index = 0, ms_delay = 0):
        vinyl = await self.vinyl_repository.get_by_tag_id(tag_id)
        if vinyl is None:
            vinyl = await self.vinyl_repository.create(tag_id, user.id)
            raise VinylCreated(vinyl.id, user.id)
        if vinyl.spotify_uri is None:
            raise VinylPending(vinyl.id, user.id)
        return await self.spotify_service.play(user,device_id,vinyl.spotify_uri,song_index,ms_delay)