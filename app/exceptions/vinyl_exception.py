from app.exceptions.base_exception import NotFoundError, AlreadyExistsError, ForbiddenError

class VinylNotFoundError(NotFoundError):
    def __init__(self, vinyl_id: int):
        super().__init__("Vinyl", vinyl_id)

class VinylForbiddenError(ForbiddenError):
    def __init__(self, vinyl_id: int, user_id: int):
        super().__init__("Vinyl", vinyl_id, user_id)