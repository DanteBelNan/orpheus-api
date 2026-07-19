from pydantic import BaseModel

class PlayRequest(BaseModel):
    device_id: str
    tag_id: str