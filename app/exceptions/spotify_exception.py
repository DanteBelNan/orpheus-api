from app.exceptions.base_exception import ExternalServiceError

class SpotifyError(ExternalServiceError):
    def __init__(self, detail: str):
        super().__init__("Spotify", detail)