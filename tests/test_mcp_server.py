from obm_rag.mcp.server import mcp_server
from obm_rag.mcp.tools import (
    execute_list_pages,
    execute_rag_search,
    execute_read_page,
)


def test_mcp_rag_search():
    # Empty query
    empty_res = execute_rag_search("")
    assert "No search query" in empty_res

    # Real query
    res = execute_rag_search("modulok konfigurációja", limit=2)
    assert "Search query:" in res
    assert "Result #1" in res
    assert "Relevance:" in res
    assert "Source file:" in res


def test_mcp_list_pages():
    pages = execute_list_pages()
    assert "Available official documentation pages:" in pages
    assert "modules.md" in pages
    assert "getting_started.rst" in pages


def test_mcp_read_page_existing():
    # Full name
    res = execute_read_page("modules.md")
    assert "=== Documentation: modules.md ===" in res
    assert "Modulok" in res

    # Without extension
    res_no_ext = execute_read_page("getting_started")
    assert "getting_started.rst" in res_no_ext


def test_mcp_read_page_security_path_traversal():
    res = execute_read_page("../../pyproject.toml")
    assert "Invalid file path" in res or "Error" in res


def test_mcp_read_page_not_found():
    res = execute_read_page("non_existent_page_12345.rst")
    assert "not found" in res


def test_mcp_server_tools_registered():
    # Verify that MCP server has registered the tools
    tools = mcp_server._tool_manager.list_tools() if hasattr(mcp_server, "_tool_manager") else []
    tool_names = [t.name for t in tools] if tools else []

    assert "rag_search" in tool_names
    assert "read_documentation_page" in tool_names
    assert "list_documentation_pages" in tool_names
