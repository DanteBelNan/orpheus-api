from pydantic import BaseModel

class ResourceResponse(BaseModel):
    spotify_uri: str
    name: str
    art_url: str | None
    resource_type: str   # "album" o "playlist"
    artist: str | None = None  # nombre del artista (albums) o dueño (playlists)

class ResourceListResponse(BaseModel):
    items: list[ResourceResponse]
    total: int