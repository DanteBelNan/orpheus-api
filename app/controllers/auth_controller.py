from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])

async def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

async def get_auth_service(repo: UserRepository = Depends(get_user_repository)) -> AuthService:
    return AuthService(repo)

#We redirect to the spotify login sendint them to our callback 
@router.get("/login")
async def login(service: AuthService = Depends(get_auth_service)):
    return RedirectResponse(url=service.get_login_url())

#Exchange Spotify code for JWT and set httpOnly cookie
@router.get("/exchange")
async def exchange(
    code: str,
    service: AuthService = Depends(get_auth_service)
):
    jwt_token, _ = await service.handle_callback(code)

    response = JSONResponse(content={"message": "Authenticated successfully"})
    response.set_cookie(
        key="access_token",
        value=jwt_token,
        httponly=True,
        samesite="lax",
        max_age=settings.jwt_expire_hours * 3600,
    )
    return response