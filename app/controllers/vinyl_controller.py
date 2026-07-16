from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.exceptions.base_exception import ForbiddenError, NotFoundError

from app.repositories.vinyl_repository import VinylRepository

from app.dtos.vinyl_dto import VinylListResponse, VinylResponse, VinylUpdateRequest

from app.services.vinyl_service import VinylService

router = APIRouter(prefix="/vinyls", tags=["Vinyl"])

async def get_vinyl_repository(db: AsyncSession = Depends(get_db)) -> VinylRepository:
    return VinylRepository(db)

async def get_vinyl_service(
        vinyl_repo: VinylRepository = Depends(get_vinyl_repository),
) -> VinylService:
    return VinylService(vinyl_repo)

#Gets all the vinyls, can use created_by and status
@router.get('/', response_model=VinylListResponse, status_code=200)
async def get_all_vinyls(
    service: VinylService = Depends(get_vinyl_service),
    current_user: User = Depends(get_current_user),
    created_by: int | None = None,
    status: str | None = None,
    page: int = 1,
    take: int = 50,
):
    return await service.get_all_vinyls(page,take,created_by,status) 

@router.get('/{vinyl_id}', response_model=VinylResponse, status_code=200)
async def get_vinyl_by_id(
    vinyl_id: int,
    service: VinylService = Depends(get_vinyl_service),
    current_user: User = Depends(get_current_user)
): 
    try:
        return await service.get_vinyl_by_id(vinyl_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404,detail=str(e))
    
@router.patch('/{vinyl_id}', response_model=VinylResponse, status_code=200)
async def update_vinyl_by_id(
    vinyl_id: int,
    body: VinylUpdateRequest,
    service: VinylService = Depends(get_vinyl_service),
    current_user: User = Depends(get_current_user),
):
    try:
        return await service.update_vinyl_by_id(vinyl_id, current_user.id, body)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))
    
@router.delete('/{vinyl_id}', status_code=204)
async def delete_vinyl_by_id(
    vinyl_id: int,
    service: VinylService = Depends(get_vinyl_service),
    current_user: User = Depends(get_current_user),
):
    try:
        await service.delete_vinyl_by_id(vinyl_id,current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))