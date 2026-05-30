from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.database import get_db
from app.repositories.device_repository import DeviceRepository
from app.services.device_service import DeviceService
from app.dtos.device_dto import DeviceRegisterRequest, DeviceResponse, DevicesListResponse
from app.dependencies import get_current_user
from app.models.user import User
from app.exceptions.base_exception import NotFoundError, AlreadyExistsError

router = APIRouter(prefix="/devices", tags=["Device"])

async def get_device_repository(db: AsyncSession = Depends(get_db)) -> DeviceRepository:
    return DeviceRepository(db)

async def get_device_service(repo: DeviceRepository = Depends(get_device_repository)) -> DeviceService:
    return DeviceService(repo)


#Creates a device
@router.post("/", response_model=DeviceResponse, status_code=201)
async def register_device(
    body: DeviceRegisterRequest,
    service: DeviceService = Depends(get_device_service),
    current_user: User = Depends(get_current_user)
):
    try:
        return await service.create_device(
            device_id=body.device_id,
            user_id=current_user.id,
            name=body.name
        )
    except AlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    
#Gets all the devices of the current user
@router.get("/", response_model=DevicesListResponse, status_code=200)
async def get_devices_of_current_user(
    service: DeviceService = Depends(get_device_service),
    current_user: User = Depends(get_current_user)      
):
    return await service.get_devices_by_user_id(
        user_id=current_user.id
    )

#Gets a specific device given his MAC id
@router.get("/{device_id}", response_model=DeviceResponse, status_code=200)
async def get_device(
        device_id: str,
        service: DeviceService = Depends(get_device_service),
        current_user: User = Depends(get_current_user)
):
    try:
        return await service.get_device_by_id(device_id=device_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
