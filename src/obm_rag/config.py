from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """OBM-RAG configuration settings."""

    # Alapértelmezett dokumentáció útvonal
    docs_path: Path = Path("documentation/official_docs/hu")

    # Vektortár perzisztálási mappa
    vector_db_path: Path = Path("data/vector_store")

    # ChromaDB kollekció neve
    collection_name: str = "obm_docs_hu"

    # FastEmbed modell
    # Opciók pl.: "BAAI/bge-m3" vagy "intfloat/multilingual-e5-small"
    embedding_model: str = "BAAI/bge-m3"

    # Chunking beállítások
    max_chunk_size: int = 700  # megközelítő szószám / tokennagyság
    chunk_overlap: int = 100

    class Config:
        env_prefix = "OBM_"


settings = Settings()
