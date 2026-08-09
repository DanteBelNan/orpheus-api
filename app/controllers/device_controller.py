from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, verify_device_key
from app.database import get_db
from app.models.user import User
from app.exceptions.base_exception import NotFoundError, AlreadyExistsError, ExternalServiceError, ForbiddenError

from app.repositories.device_repository import DeviceRepository
from app.repositories.user_repository import UserRepository

from app.dtos.device_dto import DeviceRegisterRequest, DeviceResponse, DevicesListResponse, DeviceHeartbeatResponse, DeviceHeartbeatRequest, DeviceAuthResponse

from app.services.device_service import DeviceService
from app.services.spotify_service import SpotifyService
from app.clients.spotify_client import SpotifyClient

router = APIRouter(prefix="/devices", tags=["Device"])

async def get_device_repository(db: AsyncSession = Depends(get_db)) -> DeviceRepository:
    return DeviceRepository(db)
async def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

async def get_spotify_service(
        user_repo: UserRepository = Depends(get_user_repository),
) -> SpotifyService:
    return SpotifyService(user_repo, SpotifyClient())
async def get_device_service(
        device_repo: DeviceRepository = Depends(get_device_repository),
        user_repo: UserRepository = Depends(get_user_repository),
        spotify_service: SpotifyService = Depends(get_spotify_service),
) -> DeviceService:
    return DeviceService(device_repo,user_repo, spotify_service)


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

#Gets a specific device given his MAC id (it has to be from the authenticated user)
@router.get("/{device_id}", response_model=DeviceResponse, status_code=200)
async def get_device(
        device_id: str,
        service: DeviceService = Depends(get_device_service),
        current_user: User = Depends(get_current_user)
):
    try:
        return await service.get_device_by_id(device_id=device_id,user_id=current_user.id)
    except (NotFoundError, ForbiddenError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    
@router.post("/heartbeat", response_model=DeviceHeartbeatResponse, status_code=200)
async def heartbeat(
    body: DeviceHeartbeatRequest,
    service: DeviceService = Depends(get_device_service),
    _: None = Depends(verify_device_key),
):
    try:
        return await service.process_heartbeat(device_id=body.device_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404,detail=str(e))
    except ExternalServiceError as e:
        raise HTTPException(status_code=502,detail=str(e))
    
@router.get("/auth", response_model=DeviceAuthResponse, status_code=200)
async def auth(
    device_id: str,
    service: DeviceService = Depends(get_device_service),
    _: None = Depends(verify_device_key),
):
    try:
        return await service.get_credentials(device_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404,detail=str(e))
    except ExternalServiceError as e:
        raise HTTPException(status_code=502,detail=str(e))
    
