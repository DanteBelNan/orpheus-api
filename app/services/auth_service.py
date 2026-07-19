import httpx
from datetime import datetime, timedelta
from urllib.parse import urlencode
from jose import jwt

from app.config import settings
from app.repositories.user_repository import UserRepository
from app.dtos.user_dto import SpotifyTokenData, SpotifyUserData, UserResponse
from app.exceptions.spotify_exception import SpotifyError
from app.logger import get_logger

logger = get_logger(__name__)

SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_ME_URL = "https://api.spotify.com/v1/me"
SCOPES = "user-read-email user-read-playback-state user-modify-playback-state streaming"

class AuthService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    #Builds spotify url to redirect the user
    def get_login_url(self) -> str:
        params = {
            "client_id": settings.spotify_client_id,
            "response_type": "code",
            "redirect_uri": settings.spotify_redirect_uri,
            "scope": SCOPES,
        }
        return f"{SPOTIFY_AUTH_URL}?{urlencode(params)}"
    
    async def exchange_code(self, code: str) -> SpotifyTokenData:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    SPOTIFY_TOKEN_URL,
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": settings.spotify_redirect_uri,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    auth=(settings.spotify_client_id, settings.spotify_client_secret),
                )
                response.raise_for_status()
                data = response.json()
                return SpotifyTokenData(
                    access_token=data["access_token"],
                    refresh_token=data["refresh_token"],
                    expires_in=data["expires_in"],
                )
        except httpx.HTTPStatusError:
            raise SpotifyError("Failed to exchange authorization code")
        
    #Calls GET /v1/me of Spotify API to get email and id of user
    async def get_spotify_user(self, access_token: str) -> SpotifyUserData:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    SPOTIFY_ME_URL,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                response.raise_for_status()
                data = response.json()
                return SpotifyUserData(
                    spotify_user_id=data["id"],
                    email=data["email"],
                )
        except httpx.HTTPStatusError:
            raise SpotifyError("Failed to retrieve user profile")
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
        