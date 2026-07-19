from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from app.exceptions.vinyl_exception import VinylCreated, VinylPending
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

from app.dtos.play_dto import PlayRequest

from app.services.spotify_service import SpotifyService
from app.repositories.user_repository import UserRepository
from app.repositories.vinyl_repository import VinylRepository
from app.repositories.device_repository import DeviceRepository
from app.clients.spotify_client import SpotifyClient
from app.exceptions.base_exception import ExternalServiceError
from app.services.play_service import PlayService
from app.dependencies import verify_device_key

router = APIRouter(prefix="/play", tags=["Play"])

async def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)
async def get_vinyl_repository(db: AsyncSession = Depends(get_db)) -> VinylRepository:
    return VinylRepository(db)
async def get_device_repository(db: AsyncSession = Depends(get_db)) -> DeviceRepository:
    return DeviceRepository(db)
async def get_spotify_client() -> SpotifyClient:
    return SpotifyClient()
async def get_spotify_service(
    user_repository: UserRepository = Depends(get_user_repository),
    spotify_client: SpotifyClient = Depends(get_spotify_client)
) -> SpotifyService:
    return SpotifyService(user_repository,spotify_client)
async def get_play_service(
    vinyl_repository: VinylRepository = Depends(get_vinyl_repository),
    spotify_service: SpotifyService = Depends(get_spotify_service),
) -> PlayService:
    return PlayService(vinyl_repository,spotify_service)

@router.post("/")
async def play(
    body: PlayRequest,
    play_service: PlayService = Depends(get_play_service),
    device_repo: DeviceRepository = Depends(get_device_repository),
    user_repo: UserRepository = Depends(get_user_repository),
    _: None = Depends(verify_device_key),
):
    device = await device_repo.get_by_device_id(body.device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    
    user = await user_repo.get_by_id(device.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        await play_service.play(user, body.device_id, body.tag_id)
        return JSONResponse(status_code=200, content={"status": "playing"})
    except VinylCreated as e:
        return JSONResponse(status_code=201, content={"status": "registered", "detail": str(e)})
    except VinylPending as e:
        return JSONResponse(status_code=202, content={"status": "pending", "detail": str(e)})
    except ExternalServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))