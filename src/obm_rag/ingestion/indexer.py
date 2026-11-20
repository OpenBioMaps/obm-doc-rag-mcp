import shutil
from pathlib import Path
from typing import List, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from fastembed import TextEmbedding

from obm_rag.config import settings
from obm_rag.ingestion.models import DocChunk


class DocumentIndexer:
    """Dokumentum-chunkok vektorizálása FastEmbed-del és tárolása ChromaDB-ben."""

    def __init__(
        self,
        db_path: Optional[Path] = None,
        collection_name: Optional[str] = None,
        embedding_model_name: Optional[str] = None,
    ):
        self.db_path = Path(db_path or settings.vector_db_path)
        self.collection_name = collection_name or settings.collection_name
        self.embedding_model_name = embedding_model_name or settings.embedding_model

        # FastEmbed modell inicializálása (CPU ONNX)
        self.embedding_model = TextEmbedding(model_name=self.embedding_model_name)

        # ChromaDB perzisztens kliens
        self.db_path.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=ChromaSettings(anonymized_telemetry=False),
        )

    def get_or_create_collection(self, reset: bool = False):
        """Lekéri vagy újragenerálja a ChromaDB gyűjteményt."""
        if reset:
            try:
                self.client.delete_collection(self.collection_name)
            except Exception:
                pass

        return self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine", "model": self.embedding_model_name},
        )

    def index_chunks(
        self,
        chunks: List[DocChunk],
        reset: bool = True,
        batch_size: int = 64,
    ) -> int:
        """Chunkok beágyazása és feltöltése a ChromaDB-be."""
        if not chunks:
            return 0

        collection = self.get_or_create_collection(reset=reset)

        total = len(chunks)
        # Formázott szövegek a beágyazáshoz
        texts = [c.formatted_text for c in chunks]

        # Vektorizálás FastEmbed segítségével
        embeddings_generator = self.embedding_model.embed(texts, batch_size=batch_size)
        all_embeddings = list(embeddings_generator)

        # ChromaDB feltöltése kötegekben (batch)
        for i in range(0, total, batch_size):
            end_idx = min(i + batch_size, total)
            batch_chunks = chunks[i:end_idx]
            batch_embeddings = [emb.tolist() for emb in all_embeddings[i:end_idx]]

            ids = [c.id for c in batch_chunks]
            documents = [c.formatted_text for c in batch_chunks]
            metadatas = [c.to_metadata() for c in batch_chunks]

            collection.upsert(
                ids=ids,
                documents=documents,
                embeddings=batch_embeddings,
                metadatas=metadatas,
            )

        return total
