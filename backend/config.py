from pathlib import Path
import os
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API Configuration
    PROJECT_NAME: str = "ShopLens"
    VERSION: str = "1.0.0"
    API_PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Database (Loaded from .env)
    DATABASE_URL: str = ""
    SYNC_DATABASE_URL: str = ""

    # Auth (Loaded from .env)
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Machine Learning Models
    EMBEDDING_MODEL_PATH: Path = BACKEND_DIR / "models" / "embedding_model"
    EXPECTED_EMBEDDING_DIM: int = 384
    
    # Cross-Encoder Reranker
    ENABLE_RERANKER: bool = False
    RERANKER_MODEL_NAME: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    RERANK_TOP_K: int = 30

    # Search Pipeline Defaults
    DEFAULT_RADIUS_KM: float = 5.0
    DEFAULT_LIMIT: int = 20
    RETRIEVAL_CANDIDATE_LIMIT: int = 60
    RRF_K: int = 60

    # Business Ranking Weights
    DISTANCE_PENALTY_WEIGHT: float = 0.1

settings = Settings()
