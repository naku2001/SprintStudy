# Description: Centralized environment-based runtime settings used by backend services.
# This file is part of the SprintStudy project.

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Centralized runtime settings for Gemini + Pinecone integration."""

    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    GENERATION_PROVIDER: str = os.getenv("GENERATION_PROVIDER", "gemini").lower()
    GENERATION_MODEL: str = os.getenv("GENERATION_MODEL", "")
    TOGETHER_API_KEY: str = os.getenv("TOGETHER_API_KEY", "")
    TOGETHER_BASE_URL: str = os.getenv("TOGETHER_BASE_URL", "https://api.together.xyz/v1")
    TOGETHER_MODEL: str = os.getenv("TOGETHER_MODEL", "openai/gpt-oss-120b")
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "gemini").lower()
    EMBEDDING_MODEL: str = os.getenv(
        "EMBEDDING_MODEL", "models/gemini-embedding-001"
    )
    HUGGINGFACE_API_KEY: str = os.getenv("HUGGINGFACE_API_KEY", "")
    HUGGINGFACE_API_URL: str = os.getenv("HUGGINGFACE_API_URL", "")
    CHUNK_MAX_CHARS: int = int(os.getenv("CHUNK_MAX_CHARS", "2400"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "80"))
    SUMMARY_SINGLE_PASS_MAX_CHUNKS: int = int(
        os.getenv("SUMMARY_SINGLE_PASS_MAX_CHUNKS", "80")
    )
    SUMMARY_SINGLE_PASS_MAX_INPUT_CHARS: int = int(
        os.getenv("SUMMARY_SINGLE_PASS_MAX_INPUT_CHARS", "120000")
    )
    SUMMARY_BATCH_MAX_CHUNKS: int = int(os.getenv("SUMMARY_BATCH_MAX_CHUNKS", "12"))
    SUMMARY_BATCH_MAX_CHARS: int = int(os.getenv("SUMMARY_BATCH_MAX_CHARS", "18000"))
    SUMMARY_BATCH_TARGET_COUNT: int = int(os.getenv("SUMMARY_BATCH_TARGET_COUNT", "5"))
    SUMMARY_MAX_BATCHES: int = int(os.getenv("SUMMARY_MAX_BATCHES", "5"))
    SUMMARY_BATCH_SLEEP_MS: int = int(os.getenv("SUMMARY_BATCH_SLEEP_MS", "0"))
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "sprintstudy-main")
    PINECONE_NAMESPACE: str = os.getenv("PINECONE_NAMESPACE", "default")
    PINECONE_CLOUD: str = os.getenv("PINECONE_CLOUD", "aws")
    PINECONE_REGION: str = os.getenv("PINECONE_REGION", "us-east-1")
    EMBEDDING_DIMENSION: int = int(os.getenv("EMBEDDING_DIMENSION", "768"))
    GEMINI_EMBED_MAX_BATCH: int = int(os.getenv("GEMINI_EMBED_MAX_BATCH", "100"))
    PINECONE_UPSERT_MAX_RECORDS: int = int(os.getenv("PINECONE_UPSERT_MAX_RECORDS", "60"))
    PINECONE_UPSERT_MAX_BYTES: int = int(os.getenv("PINECONE_UPSERT_MAX_BYTES", "1500000"))
    STUDY_NOTES_DIR: Path = Path(
        os.getenv("STUDY_NOTES_DIR", "backend/data/uploads_tmp")
    ).resolve()


settings = Settings()
settings.STUDY_NOTES_DIR.mkdir(parents=True, exist_ok=True)
