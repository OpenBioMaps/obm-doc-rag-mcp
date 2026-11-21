
from obm_rag.config import settings
from obm_rag.rag.retriever import DocumentationRetriever, SearchResult

# Lazy-loaded singleton retriever
_retriever: DocumentationRetriever | None = None


def get_retriever() -> DocumentationRetriever:
    """Visszaadja vagy inicializálja a singleton DocumentationRetriever példányt."""
    global _retriever
    if _retriever is None:
        _retriever = DocumentationRetriever()
    return _retriever


def execute_rag_search(query: str, limit: int = 5) -> str:
    """Szemantikus keresést hajt végre és formázott választ ad vissza."""
    query = query.strip()
    if not query:
        return "Nem adtál meg keresési kifejezést."

    retriever = get_retriever()
    results: list[SearchResult] = retriever.search(query, limit=limit)

    if not results:
        return f"Nem található releváns információ a megadott keresésre: '{query}'."

    output_blocks = [
        f"Keresési kifejezés: '{query}'",
        f"Találatok száma: {len(results)}\n",
    ]

    for idx, r in enumerate(results, 1):
        block = (
            f"--- Találat #{idx} [Relevancia: {r.score:.3f}] ---\n"
            f"Forrásfájl: {r.file_path}\n"
            f"Téma/Hierarchia: {r.doc_title} > {r.section_hierarchy}\n"
            f"Szekció címe: {r.section_title}\n"
            f"Tartalom:\n{r.content}\n"
        )
        output_blocks.append(block)

    return "\n".join(output_blocks)


def execute_read_page(file_path_str: str) -> str:
    """Biztonságosan beolvassa egy dokumentációs oldal teljes tartalmát."""
    docs_base = settings.docs_path.resolve()
    target_path = (docs_base / file_path_str).resolve()

    # Path traversal védelem: a célfájlnak a docs_base könyvtár alatt kell lennie
    if not str(target_path).startswith(str(docs_base)):
        return f"Hiba: Érvénytelen elérési út: '{file_path_str}'. Csak a dokumentációs mappán belüli fájlok érhetők el."

    if not target_path.exists() or not target_path.is_file():
        # Megpróbáljuk kiterjesztés nélkül is, ha nincs .rst / .md a végén
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
            return f"Hiba: A kért dokumentációs oldal nem található: '{file_path_str}'."

    try:
        content = target_path.read_text(encoding="utf-8", errors="replace")
        rel_path = target_path.relative_to(docs_base).as_posix()
        return f"=== Dokumentáció: {rel_path} ===\n\n{content}"
    except Exception as e:
        return f"Hiba a fájl olvasásakor ({file_path_str}): {e}"


def execute_list_pages() -> str:
    """Kilistázza a hivatalos dokumentációban elérhető fájlokat."""
    docs_base = settings.docs_path.resolve()
    if not docs_base.exists():
        return f"Hiba: A dokumentációs könyvtár nem létezik: {docs_base}"

    pages = []
    for f in sorted(docs_base.glob("**/*")):
        if f.is_file() and f.suffix.lower() in (".rst", ".md"):
            rel_path = f.relative_to(docs_base).as_posix()
            pages.append(rel_path)

    if not pages:
        return "Nem találhatók dokumentációs oldalak."

    lines = ["Elérhető hivatalos dokumentációs oldalak:"]
    for p in pages:
        lines.append(f" - {p}")

    return "\n".join(lines)
