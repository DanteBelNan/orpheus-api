from app.exceptions.base_exception import NotFoundError, AlreadyExistsError, ForbiddenError

class DeviceAlreadyRegisteredError(AlreadyExistsError):
    def __init__(self, device_id: str):
        super().__init__("Device", device_id)

class DeviceNotFoundError(NotFoundError):
    def __init__(self, device_id: str):
        super().__init__("Device", device_id)

class DeviceForbiddenError(ForbiddenError):
    def __init__(self, device_id: str, user_id: int):
        super().__init__("Device", device_id, user_id)