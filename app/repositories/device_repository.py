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
    async def get_by_user_id(self, user_id: int) -> list[Device]:
        results = await self.db.execute(
            select(Device).where(Device.user_id == user_id)
        )
        return results.scalars().all()
    
    async def get_by_device_id(self, device_id: str) -> Device:
        result = await self.db.execute(
            select(Device).where(Device.device_id == device_id)
        )
        return result.scalar_one_or_none()