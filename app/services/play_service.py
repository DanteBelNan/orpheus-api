from app.repositories.vinyl_repository import VinylRepository
from app.repositories.user_repository import UserRepository
from app.repositories.device_repository import DeviceRepository
from app.exceptions.user_exception import UserNotFoundError
from app.exceptions.device_exception import DeviceNotFoundError
from app.exceptions.base_exception import ExternalServiceError
from app.services.spotify_service import SpotifyService
from app.models.user import User
from app.exceptions.vinyl_exception import VinylPending, VinylCreated
from app.exceptions.spotify_exception import SpotifyError
from app.logger import get_logger

logger = get_logger(__name__)

class PlayService:
    def __init__(
            self, 
            vinyl_repository: VinylRepository, 
            spotify_service: SpotifyService,
            user_repository: UserRepository,
            device_repository: DeviceRepository,
        ):
        self.vinyl_repository = vinyl_repository
        self.spotify_service = spotify_service
        self.user_repository = user_repository
        self.device_repository = device_repository

    async def play(self, device_id: str, tag_id: str, song_index = 0, ms_delay = 0):
        device = await self.device_repository.get_by_device_id(device_id)
        if device is None:
            raise DeviceNotFoundError(device_id)
        
        user = await self.user_repository.get_by_id(device.user_id)
        if user is None:
            raise UserNotFoundError(device.user_id)
        logger.info("Tag scanned", extra={"tag_id": tag_id, "device_id": device_id, "user_id": user.id})


        vinyl = await self.vinyl_repository.get_by_tag_id(tag_id)
        if vinyl is None:
            vinyl = await self.vinyl_repository.create(tag_id, user.id)
            logger.info("New vinyl registered", extra={"tag_id": tag_id, "vinyl_id": vinyl.id, "user_id": user.id})
            raise VinylCreated(vinyl.id, user.id)

        if vinyl.spotify_uri is None:
            logger.info("Vinyl pending configuration", extra={"vinyl_id": vinyl.id, "tag_id": tag_id})
            raise VinylPending(vinyl.id, user.id)

        if device.spotify_device_id is None:
            raise ExternalServiceError("Spotify", "Device is not available")

        logger.info("Playing vinyl", extra={"vinyl_id": vinyl.id, "spotify_uri": vinyl.spotify_uri, "device_id": device_id})
        await self.spotify_service.play(user, device.spotify_device_id, vinyl.spotify_uri, song_index, ms_delay)
        return vinyl
    
    async def state(self, device_id: str):
        device = await self.device_repository.get_by_device_id(device_id)
        if device is None:
            raise DeviceNotFoundError(device_id)
        user = await self.user_repository.get_by_id(device.user_id)
        if user is None:
            raise UserNotFoundError(device.user_id)
        logger.info("Request state of device", extra={"device_id": device_id, "user_id": user.id})

        state_response = await self.spotify_service.state(user)
        return state_response

        