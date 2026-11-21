from obm_rag.ingestion.rst_parser import (
    clean_text,
    parse_markdown_file,
    parse_rst_file,
    split_text_into_chunks,
)


def test_clean_text():
    sample = "Első sor   \n\n\n\n\nMásodik sor  "
    cleaned = clean_text(sample)
    assert cleaned == "Első sor\n\nMásodik sor"


def test_split_text_into_chunks():
    sample = ("Ez egy hosszú bekezdés. " * 30 + "\n\n") * 5
    chunks = split_text_into_chunks(sample, max_words=50, overlap_words=10)
    assert len(chunks) > 1
    for c in chunks:
        assert len(c.split()) > 0


def test_parse_sample_md(tmp_path):
    md_file = tmp_path / "test.md"
    md_file.write_text(
        "# Főcím\n\nBevezető szöveg.\n\n## Második szint\n\nRészletek itt találhatók.",
        encoding="utf-8",
    )
    chunks = parse_markdown_file(md_file, base_docs_dir=tmp_path)
    assert len(chunks) == 2
    assert chunks[0].doc_title == "Főcím"
    assert chunks[0].section_title == "Főcím"
    assert "Bevezető szöveg" in chunks[0].content
    assert chunks[1].section_title == "Második szint"
    assert "Részletek itt" in chunks[1].content


def test_parse_sample_rst(tmp_path):
    rst_file = tmp_path / "test.rst"
    rst_file.write_text(
        "RST Főcím\n"
        "=========\n\n"
        "Bevezető az RST-hez.\n\n"
        "Alfejezet\n"
        "---------\n\n"
        "Ez egy fontos alfejezet leírása.\n",
        encoding="utf-8",
    )
    chunks = parse_rst_file(rst_file, base_docs_dir=tmp_path)
    assert len(chunks) >= 2
    assert any("RST Főcím" in c.section_hierarchy for c in chunks)
    assert any("Alfejezet" in c.section_title for c in chunks)
