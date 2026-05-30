from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.models.device import Device

class DeviceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    #Update user if doesnt exist, update if it does
    async def insert(
            self,
            device_id: str,
            user_id: int,
            name: str,
    ) -> Device:
        device = Device(
            device_id=device_id,
            user_id=user_id,
            name=name,
            created_at=datetime.utcnow()
        )
        self.db.add(device)
        await self.db.commit()
        await self.db.refresh(device)
        return device
    
    #Receives all the devices from a user
    async def get_by_user_id(self, user_id: int) -> list[Device]: #this wont need pagination, a user will never have an excesive amount of devices
        results = await self.db.execute(
            select(Device).where(Device.user_id == user_id)
        )
        return results.scalars().all()
    
    async def get_by_device_id(self, device_id: str) -> Device:
        result = await self.db.execute(
            select(Device).where(Device.device_id == device_id)
        )
        return result.scalar_one_or_none()
    
    #Updates the spotify_device_id of a device
    async def update_heartbeat(self, device_id: str, spotify_device_id: str) -> Device:
        result  = await self.db.execute(
            select(Device).where(Device.device_id == device_id)
        )
        device = result.scalar_one_or_none()
        device.spotify_device_id = spotify_device_id
        device.last_seen = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(device)
        return device
