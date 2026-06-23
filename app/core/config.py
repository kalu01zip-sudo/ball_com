from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    RAPIDAPI_KEY: str
    RAPIDAPI_HOST: str
    MONGO_URL: str
    SECRET_KEY: str
    REFRESH_SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "noreply@ball.com"
    APPLE_BUNDLE_ID: str = "com.yourcompany.app"
    ADMIN_CREATION_SECRET: str
    
    # Google Webhook Settings
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    WEBHOOK_BASE_URL: str = ""

    class Config:
        env_file = ".env"


settings = Settings()