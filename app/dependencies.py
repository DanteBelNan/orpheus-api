from fastapi import Depends, HTTPException, Cookie, Header
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.logger import get_logger

logger = get_logger(__name__)

async def get_current_user(
        access_token: str | None = Cookie(default=None),
        db: AsyncSession = Depends(get_db),
) -> User:
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = jwt.decode(access_token, settings.secret_key, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token") 
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    repo = UserRepository(db)
    user = await repo.get_by_id(int(user_id))
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

async def verify_device_key(x_device_key: str = Header(None)):
    if x_device_key != settings.device_api_key:
        logger.warning("Invalid device key attempt", extra={"provided_key_prefix": str(x_device_key)[:6] if x_device_key else "none"})
        raise HTTPException(status_code=401, detail="Invalid device key")