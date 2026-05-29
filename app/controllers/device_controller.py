from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.repositories.device_repository import DeviceRepository
from app.services.device_service import DeviceService

router = APIRouter(prefix="/devices", tags=["Device"])

async def get_device_repository(db: AsyncSession = Depends(get_db)) -> DeviceRepository:
    return DeviceRepository(db)

async def get_device_service(repo: DeviceRepository = Depends(get_device_repository)) -> DeviceService:
    return DeviceService(repo)

@router.post("/")
def registerDevice(service: DeviceService = Depends(get_device_service)):
    print("")
