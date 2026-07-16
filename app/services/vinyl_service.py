from app.repositories.vinyl_repository import VinylRepository
from app.dtos.vinyl_dto import VinylListResponse, VinylResponse
from app.exceptions.vinyl_exception import VinylNotFoundError

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