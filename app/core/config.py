from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    RAPIDAPI_KEY: str
    RAPIDAPI_HOST: str

    class Config:
        env_file = ".env"


settings = Settings()