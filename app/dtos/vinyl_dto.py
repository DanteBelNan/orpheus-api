from pydantic import BaseModel, ConfigDict, computed_field
from datetime import datetime

class VinylResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tag_id: str
    name: str | None
    spotify_uri: str | None
    album_name: str | None
    album_art_url: str | None
    created_by: int

    @computed_field
    @property
    def status(self) -> str:
        return "pending" if self.spotify_uri is None else "configured"
    
class VinylListResponse(BaseModel):
    vinyls: list[VinylResponse]
    amount: int

class VinylUpdateRequest(BaseModel):
    name: str | None = None
    spotify_uri: str
    album_name: str
    album_art_url: str