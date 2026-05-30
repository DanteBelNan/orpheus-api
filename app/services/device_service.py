import httpx
from datetime import datetime, timedelta
from app.config import settings

from app.repositories.device_repository import DeviceRepository
from app.repositories.user_repository import UserRepository
from app.dtos.device_dto import DeviceResponse, DevicesListResponse, DeviceHeartbeatResponse
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
    async def process_heartbeat(self, device_id: str) -> DeviceHeartbeatResponse:
        device = await self.device_repository.get_by_device_id(device_id)
        if device is None:
            raise DeviceNotFoundError(device_id)
        user = await self.user_repository.get_by_id(device.user_id)
        if user is None:
            raise UserNotFoundError(device.user_id) 

        access_token = await self._ensure_fresh_token(user)
        spotify_device_id = await self._get_spotify_device_id(access_token,device.name)
        await self.device_repository.update_heartbeat(device_id,spotify_device_id)

        return DeviceHeartbeatResponse(
            status="ok",
            spotify_device_id=spotify_device_id
        )

    #checks if the token of the user is fresh, if not, refreshes it with the db
    async def _ensure_fresh_token(self, user) -> str: #this may need to be a dependencie in all the endpoints that connects with raspberry
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
    
    #gets the spotify_device_id from the device
    async def  _get_spotify_device_id(self, access_token: str, device_name: str) -> str | None:
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
