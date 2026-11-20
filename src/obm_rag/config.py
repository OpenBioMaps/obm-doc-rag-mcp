from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """OBM-RAG configuration settings."""

    # Alapértelmezett dokumentáció útvonal
    docs_path: Path = Path("documentation/official_docs/hu")

    # Vektortár perzisztálási mappa
    vector_db_path: Path = Path("data/vector_store")

    # ChromaDB kollekció neve
    collection_name: str = "obm_docs_hu"

    # FastEmbed többnyelvű (magyarul is kiválóan teljesítő) modell
    # Opciók pl.: "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2" vagy "sentence-transformers/paraphrase-multilingual-mpnet-base-v2" vagy "intfloat/multilingual-e5-large"
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    # Chunking beállítások
    max_chunk_size: int = 700  # megközelítő szószám / tokennagyság
    chunk_overlap: int = 100

    model_config = SettingsConfigDict(env_prefix="OBM_")


settings = Settings()
