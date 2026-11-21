import argparse
import asyncio
import sys

from mcp.server.mcpserver import MCPServer

from obm_rag.mcp.tools import (
    execute_list_pages,
    execute_rag_search,
    execute_read_page,
)

# MCP Szerver példányosítása
mcp_server = MCPServer("OpenBioMaps-Documentation-RAG")


@mcp_server.tool(
    description=(
        "Szemantikus keresés az OpenBioMaps hivatalos magyar dokumentációjában. "
        "Visszaadja a releváns szövegrészleteket, azok témáját, fejezethierarchiáját, "
        "a forrásfájl elérési útját és relevancia pontszámát. "
        "Használd ezt az eszközt az OpenBioMaps működésével, moduljaival, szerver telepítésével, "
        "adatkezelésével, projekt létrehozásával vagy mobil kliensével kapcsolatos kérdések megválaszolására."
    )
)
def rag_search(query: str, limit: int = 5) -> str:
    """Keresés a dokumentációban."""
    return execute_rag_search(query=query, limit=limit)


@mcp_server.tool(
    description=(
        "Egy teljes OpenBioMaps dokumentációs oldal beolvasása az eredeti formájában (.rst vagy .md). "
        "Használd, ha egy adott fejezet teljes szövegére vagy konfigurációs mintájára van szükség. "
        "Példa path: 'modules.md', 'getting_started.rst', 'server_install.md'."
    )
)
def read_documentation_page(path: str) -> str:
    """Dokumentációs oldal felolvasása."""
    return execute_read_page(file_path_str=path)


@mcp_server.tool(
    description=(
        "Kilistázza az OpenBioMaps hivatalos dokumentációjában elérhető összes oldal elérési útját. "
        "Hasznos a dokumentációs struktúra áttekintéséhez."
    )
)
def list_documentation_pages() -> str:
    """Elérhető dokumentációs oldalak listázása."""
    return execute_list_pages()


@mcp_server.resource("obm://docs/pages")
def resource_list_pages() -> str:
    """Erőforrás: Dokumentációs oldalak listája."""
    return execute_list_pages()


def main():
    parser = argparse.ArgumentParser(
        description="OpenBioMaps Documentation RAG & MCP Server"
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="MCP kommunikációs protokoll (alapértelmezett: stdio)",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Szerver host SSE / HTTP mód esetén (alapértelmezett: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Szerver port SSE / HTTP mód esetén (alapértelmezett: 8000)",
    )

    args = parser.parse_args()

    # Biztosítjuk a tiszta stream kódolást
    if hasattr(sys.stdin, "reconfigure"):
        try:
            sys.stdin.reconfigure(encoding="utf-8", errors="replace")
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    if args.transport == "stdio":
        asyncio.run(mcp_server.run_stdio_async())
    elif args.transport == "sse":
        asyncio.run(mcp_server.run_sse_async(host=args.host, port=args.port))
    elif args.transport == "streamable-http":
        asyncio.run(mcp_server.run_streamable_http_async(host=args.host, port=args.port))


if __name__ == "__main__":
    main()
