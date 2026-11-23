
from obm_rag.config import settings
from obm_rag.rag.retriever import DocumentationRetriever, SearchResult

# Lazy-loaded singleton retriever
_retriever: DocumentationRetriever | None = None


def get_retriever() -> DocumentationRetriever:
    """Returns or initializes the singleton DocumentationRetriever instance."""
    global _retriever
    if _retriever is None:
        _retriever = DocumentationRetriever()
    return _retriever


def execute_rag_search(query: str, limit: int = 5) -> str:
    """Performs semantic search and returns formatted response."""
    query = query.strip()
    if not query:
        return "No search query provided."

    retriever = get_retriever()
    results: list[SearchResult] = retriever.search(query, limit=limit)

    if not results:
        return f"No relevant documentation found for query: '{query}'."

    output_blocks = [
        f"Search query: '{query}'",
        f"Results count: {len(results)}\n",
    ]

    for idx, r in enumerate(results, 1):
        block = (
            f"--- Result #{idx} [Relevance: {r.score:.3f}] ---\n"
            f"Source file: {r.file_path}\n"
            f"Topic/Hierarchy: {r.doc_title} > {r.section_hierarchy}\n"
            f"Section title: {r.section_title}\n"
            f"Content:\n{r.content}\n"
        )
        output_blocks.append(block)

    return "\n".join(output_blocks)


def execute_read_page(file_path_str: str) -> str:
    """Safely reads the full content of a documentation page."""
    docs_base = settings.docs_path.resolve()
    target_path = (docs_base / file_path_str).resolve()

    # Path traversal protection: target file must reside under docs_base
    if not str(target_path).startswith(str(docs_base)):
        return f"Error: Invalid file path: '{file_path_str}'. Only files within the documentation directory are accessible."

    if not target_path.exists() or not target_path.is_file():
        # Try appending extensions if omitted
        candidates = [
            docs_base / f"{file_path_str}.rst",
            docs_base / f"{file_path_str}.md",
        ]
        found = None
        for c in candidates:
            if c.exists() and c.is_file():
                target_path = c.resolve()
                found = True
                break
        if not found:
            return f"Error: Requested documentation page not found: '{file_path_str}'."

    try:
        content = target_path.read_text(encoding="utf-8", errors="replace")
        rel_path = target_path.relative_to(docs_base).as_posix()
        return f"=== Documentation: {rel_path} ===\n\n{content}"
    except Exception as e:
        return f"Error reading file ({file_path_str}): {e}"


def execute_list_pages() -> str:
    """Lists all available files in the official documentation."""
    docs_base = settings.docs_path.resolve()
    if not docs_base.exists():
        return f"Error: Documentation directory does not exist: {docs_base}"

    pages = []
    for f in sorted(docs_base.glob("**/*")):
        if f.is_file() and f.suffix.lower() in (".rst", ".md"):
            rel_path = f.relative_to(docs_base).as_posix()
            pages.append(rel_path)

    if not pages:
        return "No documentation pages found."

    lines = ["Available official documentation pages:"]
    for p in pages:
        lines.append(f" - {p}")

    return "\n".join(lines)
