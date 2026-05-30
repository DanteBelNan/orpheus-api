from app.exceptions.base_exception import NotFoundError

class UserNotFoundError(NotFoundError):
    def __init__(self, user_id: int):
        super().__init__("User", user_id)