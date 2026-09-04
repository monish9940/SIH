import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGODB_URI: str = os.getenv("MONGODB_URI") or os.getenv("MONGODB_URL", "mongodb+srv://admin:admin@cluster0.xa9ykft.mongodb.net/?appName=Cluster0")
    MONGODB_URL: str = os.getenv("MONGODB_URI") or os.getenv("MONGODB_URL", "mongodb+srv://admin:admin@cluster0.xa9ykft.mongodb.net/?appName=Cluster0")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "legal_metrology_compliance")
    JWT_SECRET: str = os.getenv("JWT_SECRET") or os.getenv("SECRET_KEY", "super_secret_legal_metrology_jwt_key_2026")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS") or os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173")
    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
    MAX_UPLOAD_SIZE_MB: int = 10
    PORT: int = int(os.getenv("PORT", "8090"))
    NODE_ENV: str = os.getenv("NODE_ENV", "development")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

