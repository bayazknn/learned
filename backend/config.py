import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:Kenan123.@localhost:5432/yt_learn_db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "qdrant")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY", "AIzaSyDhUZRsuoWbzphR_3nsmlV_cTURElgDvn8")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "AIzaSyAP7riVdcmE3oLWwi0USE7y_2gtzRhaw2w")
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "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")

settings = Settings()
