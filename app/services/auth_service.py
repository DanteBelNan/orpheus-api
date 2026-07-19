
from datetime import datetime, timedelta
from urllib.parse import urlencode
from jose import jwt

from app.config import settings
from app.repositories.user_repository import UserRepository
from app.dtos.user_dto import SpotifyTokenData, SpotifyUserData, UserResponse
from app.logger import get_logger
from app.clients.spotify_client import SpotifyClient

logger = get_logger(__name__)

class AuthService:
    def __init__(self, user_repository: UserRepository, spotify_client: SpotifyClient):
        self.user_repository = user_repository
        self.spotify_client = spotify_client

    #Builds spotify url to redirect the user
    def get_login_url(self) -> str:
        params = {
            "client_id": settings.spotify_client_id,
            "response_type": "code",
            "redirect_uri": settings.spotify_redirect_uri,
            "scope": settings.spotify_scopes,
        }
        return f"{settings.spotify_auth_url}?{urlencode(params)}"
    
    async def exchange_code(self, code: str) -> SpotifyTokenData:
        data = await self.spotify_client.exchange_code(code)
        return SpotifyTokenData(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            expires_in=data["expires_in"],
        )
        
    #Calls GET /v1/me of Spotify API to get email and id of user
    async def get_spotify_user(self, access_token: str) -> SpotifyUserData:
        data = await self.spotify_client.get_user_profile(access_token)
        return SpotifyUserData(
            spotify_user_id=data["id"],
            email=data["email"],
        )
    #Handles all the previous methods, upserting in db and generates jwt
    async def handle_callback(self, code: str) -> tuple[str, UserResponse]:
        token_data = await self.exchange_code(code)
        spotify_user = await self.get_spotify_user(token_data.access_token)
        token_expires_at = datetime.utcnow() + timedelta(seconds=token_data.expires_in)

        existing = await self.user_repository.get_by_spotify_id(spotify_user.spotify_user_id)
        user = await self.user_repository.upsert(
            spotify_user_id=spotify_user.spotify_user_id,
            email=spotify_user.email,
            access_token=token_data.access_token,
            refresh_token=token_data.refresh_token,
            token_expires_at=token_expires_at,
        )
        if existing:
            logger.info("User logged in", extra={"user_id": user.id, "spotify_user_id": user.spotify_user_id})
        else:
            logger.info("New user registered", extra={"user_id": user.id, "spotify_user_id": user.spotify_user_id})

        jwt_token = self._create_jwt(user.id)
        return jwt_token, UserResponse.model_validate(user)
    
    def _create_jwt(self, user_id: int) -> str:
        expire = datetime.utcnow() + timedelta(hours=settings.jwt_expire_hours)
        payload = {"sub": str(user_id), "exp": expire}
        return jwt.encode(payload,settings.secret_key,algorithm="HS256")
        