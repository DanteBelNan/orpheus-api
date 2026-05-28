from pydantic import BaseModel
from pydantic import ConfigDict
from datetime import datetime

class SpotifyUserData(BaseModel):
    spotify_user_id: str
    email: str

class SpotifyTokenData(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    spotify_user_id: str
    created_at: datetime