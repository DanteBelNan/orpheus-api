from pydantic import BaseModel

class PlayRequest(BaseModel):
    device_id: str
    tag_id: str

class StateResponse(BaseModel):
    is_playing: bool
    track_name: str
    album_name: str
    artist_name: str
    total_tracks: int
    current_track: int
    image_url: str
    duration: int
    progress: int