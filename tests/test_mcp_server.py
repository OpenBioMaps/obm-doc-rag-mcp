from obm_rag.mcp.server import mcp_server
from obm_rag.mcp.tools import (
    execute_list_pages,
    execute_rag_search,
    execute_read_page,
)


def test_mcp_rag_search():
    # Üres lekérdezés
    empty_res = execute_rag_search("")
    assert "Nem adtál meg" in empty_res

    # Valós lekérdezés
    res = execute_rag_search("modulok konfigurációja", limit=2)
    assert "Keresési kifejezés" in res
    assert "Találat #1" in res
    assert "Relevancia:" in res
    assert "Forrásfájl:" in res


def test_mcp_list_pages():
    pages = execute_list_pages()
    assert "Elérhető hivatalos dokumentációs oldalak:" in pages
    assert "modules.md" in pages
    assert "getting_started.rst" in pages


def test_mcp_read_page_existing():
    # Teljes névvel
    res = execute_read_page("modules.md")
    assert "=== Dokumentáció: modules.md ===" in res
    assert "Modulok" in res

    # Kiterjesztés nélkül
    res_no_ext = execute_read_page("getting_started")
    assert "getting_started.rst" in res_no_ext


def test_mcp_read_page_security_path_traversal():
    res = execute_read_page("../../pyproject.toml")
    assert "Érvénytelen elérési út" in res or "Hiba" in res


def test_mcp_read_page_not_found():
    res = execute_read_page("nem_letezo_oldal_12345.rst")
    assert "nem található" in res


def test_mcp_server_tools_registered():
    # Ellenőrizzük, hogy az MCP szerver regisztrálta az eszközöket
    # MCPServer belső vagy publikus tool listája
    tools = mcp_server._tool_manager.list_tools() if hasattr(mcp_server, "_tool_manager") else []
    tool_names = [t.name for t in tools] if tools else []

    assert "rag_search" in tool_names
    assert "read_documentation_page" in tool_names
    assert "list_documentation_pages" in tool_names
