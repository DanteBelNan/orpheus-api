from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.models.user import User

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_spotify_id(self, spotify_user_id: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.spotify_user_id == spotify_user_id)
        )
        return result.scalar_one_or_none()
    
    #Update user if doesnt exist, update if it does
    async def upsert(
            self,
            spotify_user_id: str,
            email: str,
            access_token: str,
            refresh_token: str,
            token_expires_at: datetime,
    ) -> User:
        user = await self.get_by_spotify_id(spotify_user_id)
        if user:
            user.spotify_access_token = access_token
            user.spotify_refresh_token = refresh_token
            user.token_expires_at = token_expires_at
            user.email = email
        else:
            user = User(
                spotify_user_id=spotify_user_id,
                email=email,
                spotify_access_token=access_token,
                spotify_refresh_token=refresh_token,
                token_expires_at=token_expires_at
            )
            self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    #Given a user id, returns the user that matches it if exists
    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()