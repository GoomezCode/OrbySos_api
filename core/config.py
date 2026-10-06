from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    db_host: str = "localhost"
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "orbyt"
    db_port: int = 3306

    jwt_secret: str = "CHANGE_ME_IN_PRODUCTION"
    jwt_algorithm: str = "HS256"
    jwt_expire_seconds: int = 3600

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # .env possui nomes legados (host/user/password/bank/port) usados por database/DataBase.py


@lru_cache
def get_settings() -> Settings:
    return Settings()
