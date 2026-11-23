from obm_rag.ingestion.rst_parser import (
    clean_text,
    parse_markdown_file,
    parse_rst_file,
    split_text_into_chunks,
)


def test_clean_text():
    sample = "First line   \n\n\n\n\nSecond line  "
    cleaned = clean_text(sample)
    assert cleaned == "First line\n\nSecond line"


def test_split_text_into_chunks():
    sample = ("This is a long paragraph. " * 30 + "\n\n") * 5
    chunks = split_text_into_chunks(sample, max_words=50, overlap_words=10)
    assert len(chunks) > 1
    for c in chunks:
        assert len(c.split()) > 0


def test_parse_sample_md(tmp_path):
    md_file = tmp_path / "test.md"
    md_file.write_text(
        "# Main Heading\n\nIntroductory text.\n\n## Second Level\n\nDetails can be found here.",
        encoding="utf-8",
    )
    chunks = parse_markdown_file(md_file, base_docs_dir=tmp_path)
    assert len(chunks) == 2
    assert chunks[0].doc_title == "Main Heading"
    assert chunks[0].section_title == "Main Heading"
    assert "Introductory text" in chunks[0].content
    assert chunks[1].section_title == "Second Level"
    assert "Details can be found here" in chunks[1].content


def test_parse_sample_rst(tmp_path):
    rst_file = tmp_path / "test.rst"
    rst_file.write_text(
        "RST Main Heading\n"
        "================\n\n"
        "Introduction to RST.\n\n"
        "Subsection\n"
        "----------\n\n"
        "Description of an important subsection.\n",
        encoding="utf-8",
    )
    chunks = parse_rst_file(rst_file, base_docs_dir=tmp_path)
    assert len(chunks) >= 2
    assert any("RST Main Heading" in c.section_hierarchy for c in chunks)
    assert any("Subsection" in c.section_title for c in chunks)
