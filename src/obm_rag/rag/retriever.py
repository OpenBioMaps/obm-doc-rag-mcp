from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings
from fastembed import TextEmbedding

from obm_rag.config import settings


@dataclass
class SearchResult:
    """A retrieved document snippet and its metadata."""

    id: str
    content: str
    file_path: str
    file_name: str
    doc_title: str
    section_title: str
    section_hierarchy: str
    score: float  # Relevance score (1 - cosine distance)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "file_path": self.file_path,
            "file_name": self.file_name,
            "doc_title": self.doc_title,
            "section_title": self.section_title,
            "section_hierarchy": self.section_hierarchy,
            "relevance_score": round(self.score, 4),
        }


class DocumentationRetriever:
    """Semantic search engine for the OpenBioMaps documentation vector database."""

    def __init__(
        self,
        db_path: Path | None = None,
        collection_name: str | None = None,
        embedding_model_name: str | None = None,
    ):
        self.db_path = Path(db_path or settings.vector_db_path)
        self.collection_name = collection_name or settings.collection_name
        self.embedding_model_name = embedding_model_name or settings.embedding_model

        if not self.db_path.exists():
            raise FileNotFoundError(
                f"Vector store directory does not exist: {self.db_path}. "
                "Run 'scripts.build_index' first!"
            )

        # Open ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        try:
            self.collection = self.client.get_collection(name=self.collection_name)
        except Exception as e:
            raise RuntimeError(
                f"Collection '{self.collection_name}' not found in ChromaDB: {e}"
            )

        # Initialize FastEmbed model for query embedding
        self.embedding_model = TextEmbedding(model_name=self.embedding_model_name)

    def search(
        self,
        query: str,
        limit: int = 5,
        where_filter: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Performs semantic search based on query."""
        query = query.strip()
        if not query:
            return []

        # Vectorize query
        query_embeddings = list(self.embedding_model.embed([query]))
        query_vector = query_embeddings[0].tolist()

        # ChromaDB query
        query_args: dict[str, Any] = {
            "query_embeddings": [query_vector],
            "n_results": limit,
            "include": ["documents", "metadatas", "distances"],
        }
        if where_filter:
            query_args["where"] = where_filter

        results = self.collection.query(**query_args)

        search_results: list[SearchResult] = []

        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for chunk_id, doc_text, meta, dist in zip(ids, documents, metadatas, distances):
            # Convert cosine distance to relevance score (1.0 = perfect match)
            # ChromaDB cosine distance: distance = 1 - cosine_similarity
            relevance = max(0.0, 1.0 - float(dist)) if dist is not None else 0.0

            search_results.append(
                SearchResult(
                    id=chunk_id,
                    content=doc_text,
                    file_path=meta.get("file_path", ""),
                    file_name=meta.get("file_name", ""),
                    doc_title=meta.get("doc_title", ""),
                    section_title=meta.get("section_title", ""),
                    section_hierarchy=meta.get("section_hierarchy", ""),
                    score=relevance,
                )
            )

        return search_results
