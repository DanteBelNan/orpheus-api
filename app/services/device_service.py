from app.repositories.device_repository import DeviceRepository
from app.repositories.user_repository import UserRepository
from app.dtos.device_dto import DeviceResponse, DevicesListResponse, DeviceHeartbeatResponse
from app.exceptions.device_exception import DeviceAlreadyRegisteredError, DeviceNotFoundError, DeviceForbiddenError
from app.exceptions.user_exception import UserNotFoundError
from app.services.spotify_service import SpotifyService
from app.logger import get_logger

logger = get_logger(__name__)

class DeviceService:
    def __init__(self, device_repository: DeviceRepository, user_repository: UserRepository, spotify_service: SpotifyService):
        self.device_repository = device_repository
        self.user_repository = user_repository
        self.spotify_service = spotify_service

    #Retrieves all the devices of a user
    async def get_devices_by_user_id(self, user_id: int) -> DevicesListResponse:
        devices = await self.device_repository.get_by_user_id(user_id)
        return DevicesListResponse(
            devices=[DeviceResponse.model_validate(d) for d in devices],
            amount=len(devices),
        )
    
    #Retrieves a device by their device_id (MAC id)
    async def get_device_by_id(self,device_id: str, user_id: int) -> DeviceResponse:
        device = await self.device_repository.get_by_device_id(device_id)
        if not device:
            raise DeviceNotFoundError(device_id)
        if device.user_id != user_id:
            raise DeviceForbiddenError(device_id,user_id)
        return DeviceResponse.model_validate(device)

    #Creates a new device
    async def create_device(self, device_id: str, user_id: int, name: str) -> DeviceResponse:
        existing = await self.device_repository.get_by_device_id(device_id)
        if existing:
            raise DeviceAlreadyRegisteredError(device_id)

        device = await self.device_repository.insert(device_id, user_id, name)
        logger.info("Device registered", extra={"device_id": device_id, "user_id": user_id, "device_name": name})
        return DeviceResponse.model_validate(device)

    #Updates the spotify_device_id of a device integrating with the spotify api
    async def process_heartbeat(self, device_id: str) -> DeviceHeartbeatResponse:
        device = await self.device_repository.get_by_device_id(device_id)
        if device is None:
            raise DeviceNotFoundError(device_id)
        user = await self.user_repository.get_by_id(device.user_id)
        if user is None:
            raise UserNotFoundError(device.user_id)

        logger.info("Heartbeat received", extra={"device_id": device_id, "user_id": user.id})

        spotify_device_id = await self.spotify_service.get_spotify_device_id(user, device.name)
        await self.device_repository.update_heartbeat(device_id, spotify_device_id)


        logger.info("Spotify device ID cached", extra={"device_id": device_id, "spotify_device_id": spotify_device_id})
        return DeviceHeartbeatResponse(
            status="ok",
            spotify_device_id=spotify_device_id
        )