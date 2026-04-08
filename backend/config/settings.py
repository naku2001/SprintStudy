import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Centralized runtime settings for Gemini + Pinecone integration."""

    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "sprintstudy-main")
    PINECONE_NAMESPACE: str = os.getenv("PINECONE_NAMESPACE", "default")
    PINECONE_CLOUD: str = os.getenv("PINECONE_CLOUD", "aws")
    PINECONE_REGION: str = os.getenv("PINECONE_REGION", "us-east-1")
    EMBEDDING_DIMENSION: int = int(os.getenv("EMBEDDING_DIMENSION", "768"))
    STUDY_NOTES_DIR: Path = Path(
        os.getenv("STUDY_NOTES_DIR", "backend/data/uploads_tmp")
    ).resolve()


settings = Settings()
settings.STUDY_NOTES_DIR.mkdir(parents=True, exist_ok=True)
