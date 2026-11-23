from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root directory (src/obm_rag/config.py -> OBM-RAG)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """OBM-RAG configuration settings."""

    # Default documentation path
    docs_path: Path = PROJECT_ROOT / "documentation" / "official_docs" / "hu"

    # Vector store persistence path
    vector_db_path: Path = PROJECT_ROOT / "data" / "vector_store"

    # ChromaDB collection name
    collection_name: str = "obm_docs_hu"

    # FastEmbed multilingual embedding model
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    # Chunking configuration
    max_chunk_size: int = 700  # approximate word count / token size
    chunk_overlap: int = 100

    model_config = SettingsConfigDict(env_prefix="OBM_")


settings = Settings()
