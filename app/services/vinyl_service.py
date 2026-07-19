from app.repositories.vinyl_repository import VinylRepository
from app.dtos.vinyl_dto import VinylListResponse, VinylResponse, VinylUpdateRequest
from app.exceptions.vinyl_exception import VinylNotFoundError, VinylForbiddenError
from app.logger import get_logger

logger = get_logger(__name__)

class VinylService:
    def __init__(self, vinyl_repository: VinylRepository):
        self.vinyl_repository = vinyl_repository

    #Retrieve all vinyls using pagination
    async def get_all_vinyls(self, page: int, take: int, created_by: int | None = None, status: str | None = None) -> VinylListResponse:
        skip = (page - 1) * take
        vinyls = await self.vinyl_repository.get_all(created_by,status,skip,take)
        return VinylListResponse(
            vinyls=[VinylResponse.model_validate(v) for v in vinyls],
            amount=len(vinyls),
        )
    
    #Retrieve a single vinyl, it can be with the tag_id or the id of the vinyl
    async def get_vinyl_by_id(self, id: int) -> VinylResponse:
        vinyl = await self.vinyl_repository.get_by_id(id)
        if vinyl is None:
            raise VinylNotFoundError(id)
        return VinylResponse.model_validate(vinyl)
    
    async def update_vinyl_by_id(self, vinyl_id: int, user_id: int, body: VinylUpdateRequest) -> VinylResponse:
        vinyl = await self.vinyl_repository.get_by_id(vinyl_id)
        if vinyl is None:
            raise VinylNotFoundError(vinyl_id)
        if vinyl.created_by != user_id:
            raise VinylForbiddenError(vinyl_id,user_id)
        updated = await self.vinyl_repository.update(vinyl_id, **body.model_dump(exclude_none=True))
        logger.info("Vinyl configured", extra={"vinyl_id": vinyl_id, "user_id": user_id, "spotify_uri": body.spotify_uri})
        return VinylResponse.model_validate(updated)

    async def delete_vinyl_by_id(self, vinyl_id: int, user_id: int) -> None:
        vinyl = await self.vinyl_repository.get_by_id(vinyl_id)
        if vinyl is None:
            raise VinylNotFoundError(vinyl_id)
        if vinyl.created_by != user_id:
            raise VinylForbiddenError(vinyl_id,user_id)
        await self.vinyl_repository.delete(vinyl_id)
        logger.info("Vinyl deleted", extra={"vinyl_id": vinyl_id, "user_id": user_id})