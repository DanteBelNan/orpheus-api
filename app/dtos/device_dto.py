from pydantic import BaseModel
from pydantic import ConfigDict
from datetime import datetime

class DeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    device_id: str
    user_id: int
    spotify_device_id: str | None
    name: str
    last_seen: datetime | None
    created_at: datetime



class DevicesListResponse(BaseModel):
    devices: list[DeviceResponse]
    amount: int

class DeviceRegisterRequest(BaseModel):
    device_id: str
    name: str



    