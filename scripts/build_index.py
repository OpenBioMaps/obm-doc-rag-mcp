import argparse
import sys
import time
from pathlib import Path

# Biztosítjuk a tiszta UTF-8 kódolást standard stream-eken
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
        "[bold cyan]OpenBioMaps Dokumentáció Indexelő[/bold cyan] indítása..."
    )
    console.print(f" - Forrás mappa: [yellow]{docs_path}[/yellow]")
    console.print(f" - Kimeneti adatbázis: [yellow]{output_dir}[/yellow]")
    console.print(f" - Embedding modell: [yellow]{model_name}[/yellow]")

    # 1. Dokumentumok beolvasása és darabolása
    with console.status("[bold green]Dokumentumok elemzése és chunkolása..."):
        t0 = time.time()
        chunks = parse_documentation_directory(docs_path)
        t_parse = time.time() - t0

    console.print(
        f"[green][+][/green] [green]{len(chunks)}[/green] darab chunk előállítva ({t_parse:.2f} mp alatt)."
    )

    if not chunks:
        console.print("[red]Hiba: Nem található feldolgozható dokumentáció![/red]")
        return

    # 2. Vektortár inicializálása és beágyazás
    with console.status("[bold green]Modell betöltése és vektorizálás CPU-n..."):
        t0 = time.time()
        indexer = DocumentIndexer(
            db_path=output_dir,
            embedding_model_name=model_name,
        )
        total_indexed = indexer.index_chunks(chunks, reset=reset)
        t_embed = time.time() - t0

    elapsed = time.time() - start_time

    # Statisztika táblázat
    table = Table(title="Indexelési Összefoglaló")
    table.add_column("Tulajdonság", style="cyan")
    table.add_column("Érték", style="magenta")

    table.add_row("Dokumentumok forrása", str(docs_path))
    table.add_row("Generált chunkok száma", str(total_indexed))
    table.add_row("Embedding modell", model_name)
    table.add_row("Parsing idő", f"{t_parse:.2f} s")
    table.add_row("Embedding + mentés idő", f"{t_embed:.2f} s")
    table.add_row("Vektorizálási sebesség", f"{total_indexed / t_embed:.1f} chunk/s")
    table.add_row("Teljes futási idő", f"{elapsed:.2f} s")

    console.print(table)
    console.print(
        f"[bold green][+] Sikeres indexelés![/bold green] Az index mentve: [cyan]{output_dir}[/cyan]\n"
    )


def main():
    parser = argparse.ArgumentParser(
        description="OpenBioMaps Dokumentáció Indexelő és Vektortár Építő"
    )
    parser.add_argument(
        "--docs-path",
        type=Path,
        default=settings.docs_path,
        help="A forrás dokumentáció könyvtára (alapértelmezett: documentation/official_docs/hu)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=settings.vector_db_path,
        help="A cél vektoradatbázis könyvtára (alapértelmezett: data/vector_store)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=settings.embedding_model,
        help="FastEmbed embedding modell (alapértelmezett: BAAI/bge-m3)",
    )
    parser.add_argument(
        "--no-reset",
        action="store_true",
        help="Ne törölje a korábbi gyűjteményt az indexelés előtt",
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
