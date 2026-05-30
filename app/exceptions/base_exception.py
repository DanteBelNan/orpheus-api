class NotFoundError(Exception):
    def __init__(self, entity: str, identifier: str | int):
        self.message = f"{entity} with id '{identifier}' not found"
        super().__init__(self.message)

class AlreadyExistsError(Exception):
    def __init__(self, entity: str, identifier: str | int):
        self.message = f"{entity} with id '{identifier}' already exists"
        super().__init__(self.message)