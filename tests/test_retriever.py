import pytest

from obm_rag.rag.retriever import DocumentationRetriever, SearchResult


@pytest.fixture(scope="module")
def retriever():
    return DocumentationRetriever()


def test_retriever_initialization(retriever):
    assert retriever.collection is not None
    assert retriever.collection.count() > 0


def test_retriever_empty_query(retriever):
    results = retriever.search("")
    assert results == []
    results_whitespace = retriever.search("   ")
    assert results_whitespace == []


def test_retriever_search_results_structure(retriever):
    results = retriever.search("modulok konfigurációja", limit=2)
    assert len(results) == 2
    for r in results:
        assert isinstance(r, SearchResult)
        assert r.id
        assert r.content
        assert r.file_path
        assert r.doc_title
        assert 0.0 <= r.score <= 1.0

        d = r.to_dict()
        assert "relevance_score" in d
        assert "content" in d
        assert "section_hierarchy" in d


def test_retriever_semantic_relevance(retriever):
    # Keresés a docker témára
    docker_results = retriever.search("docker compose telepítés", limit=3)
    assert len(docker_results) > 0
    # Legalább az egyik találatban vagy hierarchiában meg kell jelennie a docker szónak
    matched = any(
        "docker" in (r.content + r.section_hierarchy + r.doc_title).lower()
        for r in docker_results
    )
    assert matched
