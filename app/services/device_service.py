from app.repositories.device_repository import DeviceRepository
from app.repositories.user_repository import UserRepository
from app.dtos.device_dto import DeviceResponse, DevicesListResponse
from app.exceptions.device_exception import DeviceAlreadyRegisteredError, DeviceNotFoundError
from app.exceptions.user_exception import UserNotFoundError

class DeviceService:
    def __init__(self, device_repository: DeviceRepository, user_repository: UserRepository):
        self.device_repository = device_repository
        self.user_repository = user_repository

    #Retrieves all the devices of a user
    async def get_devices_by_user_id(self, user_id: int) -> DevicesListResponse:
        devices = await self.device_repository.get_by_user_id(user_id)
        return DevicesListResponse(
            devices=[DeviceResponse.model_validate(d) for d in devices],
            amount=len(devices),
        )
    
    #Retrieves a device by their device_id (MAC id)
    async def get_device_by_id(self,device_id: str) -> DeviceResponse:
        device = await self.device_repository.get_by_device_id(device_id)
        if not device:
            raise DeviceNotFoundError(device_id)
        return DeviceResponse.model_validate(device)

    #Creates a new device
    async def create_device(self, device_id: str, user_id: int, name: str) -> DeviceResponse:
        existing = await self.device_repository.get_by_device_id(device_id)
        if existing:
            raise DeviceAlreadyRegisteredError(device_id)
        
        device = await self.device_repository.insert(device_id,user_id,name)
        return DeviceResponse.model_validate(device)
    
    #Updates the spotify_device_id of a device integrating with the spotify api
    async def process_heartbeat(self, device_id: str) -> DeviceResponse:
        device = await self.device_repository.get_by_device_id(device_id)
        if device is None:
            raise DeviceNotFoundError(device_id)
        user = await self.user_repository.get_by_id(device.user_id)
        if user is None:
            raise UserNotFoundError(device.user_id) 

