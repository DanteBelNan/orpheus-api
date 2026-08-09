from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from app.exceptions.vinyl_exception import VinylCreated, VinylPending
from app.exceptions.base_exception import NotFoundError
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
    user_repository: UserRepository = Depends(get_user_repository),
    device_repository: DeviceRepository = Depends(get_device_repository)
) -> PlayService:
    return PlayService(vinyl_repository,spotify_service,user_repository,device_repository)

@router.post("/")
async def play(
    body: PlayRequest,
    play_service: PlayService = Depends(get_play_service),
    _: None = Depends(verify_device_key),
):
    try:
        vinyl = await play_service.play(body.device_id, body.tag_id)
        return JSONResponse(status_code=200, content={
            "status": "playing", 
            "vinyl": {
                    "name": vinyl.name,
                    "album": vinyl.album_name,
                    "art_url": vinyl.album_art_url,
                    "spotify_uri": vinyl.spotify_uri
                }
            })
    except VinylCreated as e:
        return JSONResponse(status_code=201, content={"status": "registered", "detail": str(e)})
    except VinylPending as e:
        return JSONResponse(status_code=202, content={"status": "pending", "detail": str(e)})
    except ExternalServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
@router.get("/state")
async def play_state(
    device_id: str,
    play_service: PlayService = Depends(get_play_service),
    _: None = Depends(verify_device_key),
):
    try:
        playStatus = await play_service.state(device_id)
        return JSONResponse(status_code=200, content=playStatus.model_dump())
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ExternalServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))
