from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.models.vinyl import Vinyl

class VinylRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    #Retrieves a vinyl by vinyl_id
    async def get_by_id(self, vinyl_id: int) -> Vinyl:
        result = await self.db.execute(
            select(Vinyl).where(Vinyl.id == vinyl_id)
        )
        return result.scalar_one_or_none()

    async def get_by_tag_id(self, tag_id: str) -> Vinyl:
        result = await self.db.execute(
            select(Vinyl).where(Vinyl.tag_id == tag_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_created_by(self, created_by: int) -> list[Vinyl]:
        results = await self.db.execute(
            select(Vinyl).where(Vinyl.created_by == created_by)
        )
        return results.scalars().all()
    
    async def get_all(
        self, 
        created_by: int | None = None,
        status: str | None = None, 
        skip: int = 0, 
        limit: int = 50
    ) -> list[Vinyl]:
        query = select(Vinyl).order_by(Vinyl.created_at)
        if created_by is not None:
            query = query.where(Vinyl.created_by == created_by)
        if status == "pending":
            query = query.where(Vinyl.spotify_uri == None)
        if status == "configured":
            query = query.where(Vinyl.spotify_uri != None)
            
        results = await self.db.execute(
            query.limit(limit).offset(skip)
        )
        return results.scalars().all()
    async def create(self, tag_id: str, created_by: int, name: str | None = None) -> Vinyl:
        vinyl = Vinyl(
            tag_id=tag_id,
            created_by=created_by,
            name=name,
            created_at=datetime.utcnow()
        )
        self.db.add(vinyl)
        await self.db.commit()
        await self.db.refresh(vinyl)
        return vinyl
    
    async def update(self, vinyl_id: int, **fields) -> Vinyl:
        vinyl = await self.get_by_id(vinyl_id)
        for key,value in fields.items():
            setattr(vinyl, key, value)
        #maybe we can add a history of previous changes of a vinyl!
        await self.db.commit()
        await self.db.refresh(vinyl)
        return vinyl
    
    async def delete(self, vinyl_id: int) -> None: #this probably wont be used, but its safe to have it in case we need it
        vinyl = await self.get_by_id(vinyl_id)
        if vinyl:
            await self.db.delete(vinyl)
            await self.db.commit()
    