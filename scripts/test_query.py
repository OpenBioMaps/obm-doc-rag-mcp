import argparse
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel

from obm_rag.rag.retriever import DocumentationRetriever

console = Console(highlight=False)


def display_results(query: str, results, elapsed: float):
    console.print(f"\n[bold cyan]Search query:[/bold cyan] [yellow]{query}[/yellow]")
    console.print(f"Results count: [bold green]{len(results)}[/bold green] (latency: {elapsed:.3f} s)\n")

    if not results:
        console.print("[red]No relevant results found.[/red]\n")
        return

    for idx, r in enumerate(results, 1):
        header = (
            f"[bold green]#{idx}[/bold green] | "
            f"[bold magenta]{r.doc_title}[/bold magenta] > "
            f"[cyan]{r.section_hierarchy}[/cyan] "
            f"([yellow]Relevance: {r.score:.3f}[/yellow])\n"
            f"[dim]Source: {r.file_path} (ID: {r.id})[/dim]"
        )
        content_preview = r.content.strip()
        console.print(
            Panel(
                content_preview,
                title=header,
                title_align="left",
                border_style="blue",
            )
        )
    console.print()


def main():
    parser = argparse.ArgumentParser(
        description="OpenBioMaps Documentation Semantic Search Test"
    )
    parser.add_argument(
        "query",
        type=str,
        nargs="?",
        help="Search query or question (if omitted, interactive mode starts)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=3,
        help="Number of results to display (default: 3)",
    )
    args = parser.parse_args()

    try:
        retriever = DocumentationRetriever()
    except Exception as e:
        console.print(f"[bold red]Error initializing retriever:[/bold red] {e}")
        sys.exit(1)

    if args.query:
        t0 = time.time()
        results = retriever.search(args.query, limit=args.limit)
        display_results(args.query, results, time.time() - t0)
    else:
        console.print("[bold green]OpenBioMaps Interactive Documentation Search[/bold green]")
        console.print("Type your question, or press Enter / 'exit' to quit.\n")
        while True:
            try:
                user_query = console.input("[bold cyan]Query > [/bold cyan]").strip()
            except (KeyboardInterrupt, EOFError):
                break
            if not user_query or user_query.lower() in ("exit", "quit", "q"):
                break
            t0 = time.time()
            results = retriever.search(user_query, limit=args.limit)
            display_results(user_query, results, time.time() - t0)


if __name__ == "__main__":
    main()
