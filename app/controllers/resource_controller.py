from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user
from app.database import get_db
from app.models.user import User

from app.dtos.resource_dto import ResourceListResponse

from app.services.spotify_service import SpotifyService
from app.repositories.user_repository import UserRepository
from app.clients.spotify_client import SpotifyClient
from app.exceptions.base_exception import ExternalServiceError

router = APIRouter(prefix="/resources", tags=["Resource"])

async def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)
async def get_spotify_client() -> SpotifyClient:
    return SpotifyClient()
async def get_spotify_service(
    user_repository: UserRepository = Depends(get_user_repository),
    spotify_client: SpotifyClient = Depends(get_spotify_client)
) -> SpotifyService:
    return SpotifyService(user_repository,spotify_client)

@router.get("/search", response_model=ResourceListResponse, status_code=200)
async def search_resources(
    query: str,
    current_user: User = Depends(get_current_user),
    spotify_service: SpotifyService = Depends(get_spotify_service),
    resource_type: str = "album,playlist"
):
    try:
        return await spotify_service.search(current_user,query,resource_type)
    except ExternalServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))