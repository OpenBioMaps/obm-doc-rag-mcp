from dataclasses import dataclass
from typing import Any


@dataclass
class DocChunk:
    """A document text chunk and its associated metadata."""

    id: str
    content: str
    file_path: str
    file_name: str
    doc_title: str
    section_title: str
    section_hierarchy: str
    chunk_index: int
    total_chunks: int = 1

    def to_metadata(self) -> dict[str, Any]:
        """Returns metadata serializable to vector store."""
        return {
            "file_path": self.file_path,
            "file_name": self.file_name,
            "doc_title": self.doc_title,
            "section_title": self.section_title,
            "section_hierarchy": self.section_hierarchy,
            "chunk_index": self.chunk_index,
        }

    @property
    def formatted_text(self) -> str:
        """Formatted and labeled text prepared for embedding and LLM context."""
        header = f"[{self.doc_title}] > {self.section_hierarchy}\n" if self.section_hierarchy else f"[{self.doc_title}]\n"
        return f"{header}{self.content.strip()}"
