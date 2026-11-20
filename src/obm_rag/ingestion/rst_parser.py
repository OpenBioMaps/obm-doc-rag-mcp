import re
from pathlib import Path
from typing import List, Tuple, Optional
from docutils.core import publish_doctree
from docutils.parsers.rst import roles, directives, Directive
from docutils import nodes

from obm_rag.ingestion.models import DocChunk


class _SphinxDummyDirective(Directive):
    """Csendes kezelő Sphinx direktívákhoz (pl. toctree, note, warning)."""

    has_content = True
    optional_arguments = 10
    final_argument_whitespace = True
    option_spec = {}

    def run(self):
        # A direktíva tartalmát (ha van szövege) bekezdésként megőrizzük
        text = "\n".join(self.content).strip()
        if text:
            return [nodes.paragraph(text, text)]
        return []


# Regisztráljuk a leggyakoribb Sphinx direktívákat
_SPHINX_DIRECTIVES = [
    "toctree",
    "note",
    "warning",
    "tip",
    "hint",
    "important",
    "caution",
    "seealso",
    "versionadded",
    "versionchanged",
    "deprecated",
    "highlight",
    "code-block",
    "sourcecode",
    "literalinclude",
    "glossary",
    "index",
    "figure",
    "image",
]
for dir_name in _SPHINX_DIRECTIVES:
    directives.register_directive(dir_name, _SphinxDummyDirective)


def _sphinx_role_handler(name, rawtext, text, lineno, inliner, options=None, content=None):
    """Kezeli a Sphinx-specifikus role-okat (:doc:, :ref:, :term: stb.)."""
    if options is None:
        options = {}
    if content is None:
        content = []
    # Ha van 'Szöveg <hivatkozás>' formátum, csak a megjelenő szöveget tartjuk meg
    if "<" in text and text.endswith(">"):
        display_text = text[: text.index("<")].strip()
    else:
        display_text = text.strip()
    return [nodes.Text(display_text)], []


# Regisztráljuk az ismert Sphinx role-okat docutils alatt
_SPHINX_ROLES = [
    "doc",
    "ref",
    "download",
    "term",
    "file",
    "command",
    "menuselection",
    "guilabel",
    "kbd",
    "program",
    "option",
    "envvar",
]
for role_name in _SPHINX_ROLES:
    roles.register_local_role(role_name, _sphinx_role_handler)


def clean_text(text: str) -> str:
    """Többszörös szóközök és üres sorok tisztítása."""
    lines = [line.rstrip() for line in text.splitlines()]
    cleaned = "\n".join(lines)
    # 3 vagy több üres sor redukálása legfeljebb kettőre
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def split_text_into_chunks(
    text: str, max_words: int = 500, overlap_words: int = 80
) -> List[str]:
    """Hosszú szöveget bekezdések vagy mondatok mentén bont kisebb részekre átfedéssel."""
    text = clean_text(text)
    words = text.split()
    if len(words) <= max_words:
        return [text] if text else []

    chunks = []
    # Elsődleges bontás bekezdések szerint
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    current_chunk: List[str] = []
    current_word_count = 0

    for para in paragraphs:
        para_words = len(para.split())
        if current_word_count + para_words > max_words and current_chunk:
            chunk_str = "\n\n".join(current_chunk)
            chunks.append(chunk_str)

            # Átfedés megtartása
            overlap_collector: List[str] = []
            overlap_count = 0
            for prev_para in reversed(current_chunk):
                p_len = len(prev_para.split())
                if overlap_count + p_len <= overlap_words or not overlap_collector:
                    overlap_collector.insert(0, prev_para)
                    overlap_count += p_len
                else:
                    break
            current_chunk = overlap_collector
            current_word_count = sum(len(p.split()) for p in current_chunk)

        current_chunk.append(para)
        current_word_count += para_words

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks


def parse_rst_file(file_path: Path, base_docs_dir: Optional[Path] = None) -> List[DocChunk]:
    """Beolvas egy Sphinx .rst fájlt és szekció-alapú chunk-okat készít."""
    rel_path = (
        file_path.relative_to(base_docs_dir).as_posix()
        if base_docs_dir
        else file_path.name
    )
    raw_content = file_path.read_text(encoding="utf-8", errors="replace")

    # Előtisztítás: docinfo mezők kiszűrése ha vannak
    cleaned_input = re.sub(r"^:author:.*$", "", raw_content, flags=re.MULTILINE)
    cleaned_input = re.sub(r"^:date:.*$", "", cleaned_input, flags=re.MULTILINE)

    try:
        doctree = publish_doctree(
            cleaned_input,
            settings_overrides={
                "report_level": 5,
                "halt_level": 6,
                "warning_stream": None,
            },
        )
    except Exception:
        # Ha a docutils nem tudja értelmezni, fallback egyszerű szövegbontásra
        return _fallback_parse_file(file_path, rel_path, raw_content)

    doc_title = file_path.stem
    sections = list(doctree.findall(lambda n: n.tagname == "section"))

    if not sections:
        # Ha nincsenek szekciók, az egész dokumentum szövege egy vagy több chunk
        full_text = clean_text(doctree.astext())
        return _create_chunks_from_text(
            full_text=full_text,
            doc_title=doc_title,
            section_title="Főoldal",
            section_hierarchy=doc_title,
            file_path=rel_path,
            file_name=file_path.name,
        )

    chunks: List[DocChunk] = []

    # Megkeressük a legfelső szintű címet
    first_title_node = doctree.next_node(lambda n: n.tagname == "title")
    if first_title_node:
        doc_title = first_title_node.astext().strip()

    # Gyűjtsük ki a dokumentum gyökér szintjén lévő bevezető szöveget (még az alfejezetek előtt)
    intro_parts = []
    for child in doctree.children:
        if child.tagname not in ("section", "title", "docinfo"):
            intro_parts.append(child.astext())
    intro_text = clean_text("\n\n".join(intro_parts))
    if intro_text:
        chunks.extend(
            _create_chunks_from_text(
                full_text=intro_text,
                doc_title=doc_title,
                section_title="Bevezetés",
                section_hierarchy=doc_title,
                file_path=rel_path,
                file_name=file_path.name,
            )
        )

    # Végigmegyünk a szekciókon
    for sec in sections:
        title_node = sec.next_node(lambda n: n.tagname == "title")
        section_title = title_node.astext().strip() if title_node else "Általános"

        # Felépítjük a szekció hierarchiát a szülőkből
        hierarchy_parts = []
        parent = sec.parent
        while parent and parent.tagname == "section":
            p_title = parent.next_node(lambda n: n.tagname == "title")
            if p_title:
                hierarchy_parts.insert(0, p_title.astext().strip())
            parent = parent.parent

        if not hierarchy_parts:
            hierarchy_parts = [doc_title]
        hierarchy_parts.append(section_title)
        section_hierarchy = " > ".join(dict.fromkeys(hierarchy_parts))  # ismétlődések nélkül

        # A szekció közvetlen szöveges tartalma (kihagyva a beágyazott alszekciók tartalmát,
        # mert azokat külön szekcióként úgyis bejárjuk)
        sec_text_parts = []
        for child in sec.children:
            if child.tagname not in ("section", "title"):
                sec_text_parts.append(child.astext())

        sec_text = clean_text("\n\n".join(sec_text_parts))
        if not sec_text:
            continue

        sec_chunks = _create_chunks_from_text(
            full_text=sec_text,
            doc_title=doc_title,
            section_title=section_title,
            section_hierarchy=section_hierarchy,
            file_path=rel_path,
            file_name=file_path.name,
        )
        chunks.extend(sec_chunks)

    # Indexek újraszámozása a fájl szintjén
    for idx, c in enumerate(chunks):
        c.chunk_index = idx
        c.total_chunks = len(chunks)
        c.id = f"{Path(rel_path).stem}_{idx}"

    return chunks


def parse_markdown_file(
    file_path: Path, base_docs_dir: Optional[Path] = None
) -> List[DocChunk]:
    """Beolvas egy Markdown (.md) fájlt és szekció-alapú chunk-okat készít."""
    rel_path = (
        file_path.relative_to(base_docs_dir).as_posix()
        if base_docs_dir
        else file_path.name
    )
    raw_content = file_path.read_text(encoding="utf-8", errors="replace")

    lines = raw_content.splitlines()
    doc_title = file_path.stem

    sections: List[Tuple[str, List[str], str]] = []  # (section_title, lines, hierarchy)
    current_title = "Általános"
    current_lines: List[str] = []
    hierarchy_stack: List[Tuple[int, str]] = []

    for line in lines:
        header_match = re.match(r"^(#{1,6})\s+(.*)$", line)
        if header_match:
            level = len(header_match.group(1))
            title = header_match.group(2).strip()

            if level == 1 and doc_title == file_path.stem:
                doc_title = title

            # Előző szekció lezárása
            if current_lines:
                hierarchy_str = " > ".join([h[1] for h in hierarchy_stack]) if hierarchy_stack else doc_title
                sections.append((current_title, current_lines, hierarchy_str))
                current_lines = []

            # Hierarchia frissítése
            while hierarchy_stack and hierarchy_stack[-1][0] >= level:
                hierarchy_stack.pop()
            hierarchy_stack.append((level, title))

            current_title = title
        else:
            current_lines.append(line)

    if current_lines:
        hierarchy_str = " > ".join([h[1] for h in hierarchy_stack]) if hierarchy_stack else doc_title
        sections.append((current_title, current_lines, hierarchy_str))

    chunks: List[DocChunk] = []
    for s_title, s_lines, s_hier in sections:
        sec_text = clean_text("\n".join(s_lines))
        if not sec_text:
            continue
        sec_chunks = _create_chunks_from_text(
            full_text=sec_text,
            doc_title=doc_title,
            section_title=s_title,
            section_hierarchy=s_hier,
            file_path=rel_path,
            file_name=file_path.name,
        )
        chunks.extend(sec_chunks)

    # Indexek újraszámozása
    for idx, c in enumerate(chunks):
        c.chunk_index = idx
        c.total_chunks = len(chunks)
        c.id = f"{Path(rel_path).stem}_{idx}"

    return chunks


def _fallback_parse_file(
    file_path: Path, rel_path: str, raw_content: str
) -> List[DocChunk]:
    """Egyszerű szövegbontás, ha nem parse-olható strukturáltan."""
    doc_title = file_path.stem
    cleaned = clean_text(raw_content)
    return _create_chunks_from_text(
        full_text=cleaned,
        doc_title=doc_title,
        section_title="Általános",
        section_hierarchy=doc_title,
        file_path=rel_path,
        file_name=file_path.name,
    )


def _create_chunks_from_text(
    full_text: str,
    doc_title: str,
    section_title: str,
    section_hierarchy: str,
    file_path: str,
    file_name: str,
    min_words: int = 1,
) -> List[DocChunk]:
    """Szövegből DocChunk objektumokat állít elő, kiszűrve a teljesen üres töredékeket."""
    text_chunks = split_text_into_chunks(full_text)
    result = []
    for idx, piece in enumerate(text_chunks):
        if len(piece.split()) < min_words:
            continue
        chunk = DocChunk(
            id=f"{Path(file_path).stem}_{idx}",
            content=piece,
            file_path=file_path,
            file_name=file_name,
            doc_title=doc_title,
            section_title=section_title,
            section_hierarchy=section_hierarchy,
            chunk_index=idx,
            total_chunks=len(text_chunks),
        )
        result.append(chunk)
    return result


def parse_documentation_directory(docs_dir: Path) -> List[DocChunk]:
    """Beolvassa a megadott könyvtár összes .rst és .md dokumentáció fájlját."""
    docs_dir = Path(docs_dir)
    if not docs_dir.exists():
        raise FileNotFoundError(f"Dokumentáció mappa nem található: {docs_dir}")

    all_chunks: List[DocChunk] = []

    # Rendezett sorrendben járjuk be
    for file_path in sorted(docs_dir.glob("**/*")):
        if file_path.is_file():
            if file_path.suffix.lower() == ".rst":
                chunks = parse_rst_file(file_path, base_docs_dir=docs_dir)
                all_chunks.extend(chunks)
            elif file_path.suffix.lower() == ".md":
                chunks = parse_markdown_file(file_path, base_docs_dir=docs_dir)
                all_chunks.extend(chunks)

    # Globális egyedi azonosítók hozzárendelése
    for i, chk in enumerate(all_chunks):
        chk.id = f"chunk_{i:04d}_{chk.file_name.replace('.', '_')}"

    return all_chunks
