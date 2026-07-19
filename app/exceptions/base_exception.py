class NotFoundError(Exception):
    def __init__(self, entity: str, identifier: str | int):
        self.message = f"{entity} with id '{identifier}' not found"
        super().__init__(self.message)

class AlreadyExistsError(Exception):
    def __init__(self, entity: str, identifier: str | int):
        self.message = f"{entity} with id '{identifier}' already exists"
        super().__init__(self.message)

class ExternalServiceError(Exception):
    def __init__(self, service: str, detail: str):
        self.message = f"{service} error: {detail}"
        super().__init__(self.message)

class ForbiddenError(Exception):
    def __init__(self, entity: str, identifier: str | int, user_id: int):
        self.message = f"{entity} with id '{identifier}' cannot be modified by user '{user_id}'"
        super().__init__(self.message)

class PendingError(Exception):
    def __init__(self, entity: str, identifier: str | int, user_id: int):
        self.message = f"{entity} with id '{identifier}' created by user '{user_id}' is still pending"
        super().__init__(self.message)

class Registered(Exception):
    def __init__(self, entity: str, identifier: str | int, user_id: int):
        self.message = f"{entity} with id '{identifier}' was created by user '{user_id}'"
        super().__init__(self.message)