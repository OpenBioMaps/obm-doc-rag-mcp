import argparse
import asyncio
import sys

from mcp.server.mcpserver import MCPServer

from obm_rag.mcp.tools import (
    execute_list_pages,
    execute_rag_search,
    execute_read_page,
)

# Instantiate MCP Server
mcp_server = MCPServer("OpenBioMaps-Documentation-RAG")


@mcp_server.tool(
    description=(
        "Semantic search in official OpenBioMaps documentation. "
        "Returns relevant documentation snippets, topics, section hierarchy, "
        "source file paths, and relevance scores. "
        "Use this tool to answer questions regarding OpenBioMaps features, modules, server installation, "
        "data management, project setup, or the mobile client."
    )
)
def rag_search(query: str, limit: int = 5) -> str:
    """Search the documentation."""
    return execute_rag_search(query=query, limit=limit)


@mcp_server.tool(
    description=(
        "Read a complete OpenBioMaps documentation page in its raw format (.rst or .md). "
        "Use when the full text of a chapter or configuration example is needed. "
        "Example paths: 'modules.md', 'getting_started.rst', 'server_install.md'."
    )
)
def read_documentation_page(path: str) -> str:
    """Read full documentation page."""
    return execute_read_page(file_path_str=path)


@mcp_server.tool(
    description=(
        "List all available page paths in official OpenBioMaps documentation. "
        "Useful for exploring documentation structure."
    )
)
def list_documentation_pages() -> str:
    """List available documentation pages."""
    return execute_list_pages()


@mcp_server.resource("obm://docs/pages")
def resource_list_pages() -> str:
    """Resource: List of documentation pages."""
    return execute_list_pages()


def main():
    parser = argparse.ArgumentParser(
        description="OpenBioMaps Documentation RAG & MCP Server"
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="MCP communication transport (default: stdio)",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Server host for SSE / HTTP mode (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Server port for SSE / HTTP mode (default: 8000)",
    )

    args = parser.parse_args()

    # Ensure clean stream encoding
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
