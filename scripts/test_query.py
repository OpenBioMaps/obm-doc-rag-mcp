import argparse
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from obm_rag.rag.retriever import DocumentationRetriever

console = Console(highlight=False)


def display_results(query: str, results, elapsed: float):
    console.print(f"\n[bold cyan]Keresési kifejezés:[/bold cyan] [yellow]{query}[/yellow]")
    console.print(f"Találatok száma: [bold green]{len(results)}[/bold green] (lekérdezési idő: {elapsed:.3f} mp)\n")

    if not results:
        console.print("[red]Nem található releváns találat.[/red]\n")
        return

    for idx, r in enumerate(results, 1):
        header = (
            f"[bold green]#{idx}[/bold green] | "
            f"[bold magenta]{r.doc_title}[/bold magenta] > "
            f"[cyan]{r.section_hierarchy}[/cyan] "
            f"([yellow]Relevancia: {r.score:.3f}[/yellow])\n"
            f"[dim]Forrás: {r.file_path} (ID: {r.id})[/dim]"
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
        description="OpenBioMaps Dokumentáció Szemantikus Kereső Teszt"
    )
    parser.add_argument(
        "query",
        type=str,
        nargs="?",
        help="A keresendő kérdés vagy kifejezés (ha üres, interaktív mód indul)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=3,
        help="A megjelenítendő találatok száma (alapértelmezett: 3)",
    )
    args = parser.parse_args()

    try:
        retriever = DocumentationRetriever()
    except Exception as e:
        console.print(f"[bold red]Hiba a retriever inicializálásakor:[/bold red] {e}")
        sys.exit(1)

    if args.query:
        t0 = time.time()
        results = retriever.search(args.query, limit=args.limit)
        display_results(args.query, results, time.time() - t0)
    else:
        console.print("[bold green]OpenBioMaps Interaktív Dokumentáció Kereső[/bold green]")
        console.print("Írj be egy kérdést, vagy nyomj Entert üresen / 'exit' a kilépéshez.\n")
        while True:
            try:
                user_query = console.input("[bold cyan]Kérdés > [/bold cyan]").strip()
            except (KeyboardInterrupt, EOFError):
                break
            if not user_query or user_query.lower() in ("exit", "quit", "q"):
                break
            t0 = time.time()
            results = retriever.search(user_query, limit=args.limit)
            display_results(user_query, results, time.time() - t0)


if __name__ == "__main__":
    main()
