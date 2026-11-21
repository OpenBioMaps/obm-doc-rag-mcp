from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Projekt gyökérkönyvtára (src/obm_rag/config.py -> OBM-RAG)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """OBM-RAG configuration settings."""

    # Alapértelmezett dokumentáció útvonal
    docs_path: Path = PROJECT_ROOT / "documentation" / "official_docs" / "hu"

    # Vektortár perzisztálási mappa
    vector_db_path: Path = PROJECT_ROOT / "data" / "vector_store"

    # ChromaDB kollekció neve
    collection_name: str = "obm_docs_hu"

    # FastEmbed többnyelvű (magyarul is kiválóan teljesítő) modell
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    # Chunking beállítások
    max_chunk_size: int = 700  # megközelítő szószám / tokennagyság
    chunk_overlap: int = 100

    model_config = SettingsConfigDict(env_prefix="OBM_")


settings = Settings()
