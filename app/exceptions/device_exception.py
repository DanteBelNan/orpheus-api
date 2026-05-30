from app.exceptions.base_exception import NotFoundError, AlreadyExistsError

class DeviceAlreadyRegisteredError(AlreadyExistsError):
    def __init__(self, device_id: str):
        super().__init__("Device", device_id)

class DeviceNotFoundError(NotFoundError):
    def __init__(self, device_id: str):
        super().__init__("Device", device_id)