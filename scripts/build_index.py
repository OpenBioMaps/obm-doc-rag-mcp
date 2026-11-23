import argparse
import sys
import time
from pathlib import Path

# Ensure clean UTF-8 encoding on standard streams
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from rich.console import Console
from rich.table import Table

from obm_rag.config import settings
from obm_rag.ingestion.indexer import DocumentIndexer
from obm_rag.ingestion.rst_parser import parse_documentation_directory

console = Console(highlight=False)


def build_index(
    docs_path: Path,
    output_dir: Path,
    model_name: str,
    reset: bool = True,
):
    start_time = time.time()
    console.print(
        "[bold cyan]OpenBioMaps Documentation Indexer[/bold cyan] starting..."
    )
    console.print(f" - Source directory: [yellow]{docs_path}[/yellow]")
    console.print(f" - Output vector database: [yellow]{output_dir}[/yellow]")
    console.print(f" - Embedding model: [yellow]{model_name}[/yellow]")

    # 1. Read and chunk documents
    with console.status("[bold green]Parsing and chunking documents..."):
        t0 = time.time()
        chunks = parse_documentation_directory(docs_path)
        t_parse = time.time() - t0

    console.print(
        f"[green][+][/green] [green]{len(chunks)}[/green] chunks generated in {t_parse:.2f} s."
    )

    if not chunks:
        console.print("[red]Error: No parseable documentation found![/red]")
        return

    # 2. Initialize vector store and compute embeddings
    with console.status("[bold green]Loading model and vectorizing on CPU..."):
        t0 = time.time()
        indexer = DocumentIndexer(
            db_path=output_dir,
            embedding_model_name=model_name,
        )
        total_indexed = indexer.index_chunks(chunks, reset=reset)
        t_embed = time.time() - t0

    elapsed = time.time() - start_time

    # Summary table
    table = Table(title="Indexing Summary")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="magenta")

    table.add_row("Documentation source", str(docs_path))
    table.add_row("Total generated chunks", str(total_indexed))
    table.add_row("Embedding model", model_name)
    table.add_row("Parsing time", f"{t_parse:.2f} s")
    table.add_row("Embedding + save time", f"{t_embed:.2f} s")
    table.add_row("Vectorization throughput", f"{total_indexed / t_embed:.1f} chunks/s")
    table.add_row("Total elapsed time", f"{elapsed:.2f} s")

    console.print(table)
    console.print(
        f"[bold green][+] Indexing successful![/bold green] Index saved to: [cyan]{output_dir}[/cyan]\n"
    )


def main():
    parser = argparse.ArgumentParser(
        description="OpenBioMaps Documentation Indexer and Vector Store Builder"
    )
    parser.add_argument(
        "--docs-path",
        type=Path,
        default=settings.docs_path,
        help="Source documentation directory (default: documentation/official_docs/hu)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=settings.vector_db_path,
        help="Target vector database directory (default: data/vector_store)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=settings.embedding_model,
        help="FastEmbed embedding model (default: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2)",
    )
    parser.add_argument(
        "--no-reset",
        action="store_true",
        help="Do not delete existing collection before indexing",
    )

    args = parser.parse_args()
    build_index(
        docs_path=args.docs_path,
        output_dir=args.output_dir,
        model_name=args.model,
        reset=not args.no_reset,
    )


if __name__ == "__main__":
    main()
