from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env",env_file_encoding="utf-8")

    #Spotify
    spotify_client_id: str
    spotify_client_secret: str
    spotify_redirect_uri: str

    #DB
    mysql_host: str
    mysql_port: int = 3306
    mysql_user: str
    mysql_password: str
    mysql_database: str
    
    #JWT
    secret_key: str
    jwt_expire_hours: int = 12

    @property
    def database_url(self) -> str:
        usr = self.mysql_user
        pwd = self.mysql_password
        host = self.mysql_host
        port = self.mysql_port
        database = self.mysql_database
        return (f"mysql+aiomysql://{usr}:{pwd}@{host}:{port}/{database}")
    
settings = Settings()