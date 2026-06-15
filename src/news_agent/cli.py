"""Command-line entry point (Typer)."""

# Builtin imports
from datetime import UTC, datetime

# Project specific imports
import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

# Local imports
from .config import load_config
from .fetch import fetch_all
from .logger import get_logger
from .rank import rank_items
from .summarize import build_provider, summarize_ranked

LOG = get_logger(__name__)

app = typer.Typer(help="Daily news digest agent.", no_args_is_help=True)


@app.callback()
def _root() -> None:
    """Daily news digest agent — see the subcommands below."""


@app.command()
def run(config: str = "config.yaml") -> None:
    """Run the digest pipeline once (fetch -> rank -> summarize -> email)."""
    cfg = load_config(config)
    LOG.info(
        "config loaded",
        categories=list(cfg.categories),
        top_n=cfg.top_n_per_category,
        llm_provider=cfg.llm.provider,
        llm_model=cfg.llm.model,
    )
    typer.echo("Scaffold stage — pipeline not implemented yet.")


@app.command()
def fetch(config: str = "config.yaml", category: str | None = None) -> None:
    """Fetch all sources and print the raw items (no ranking yet)."""
    cfg = load_config(config)
    categories = [category] if category else None
    items = fetch_all(cfg, categories)

    table = Table(title=f"Fetched {len(items)} items")
    table.add_column("category", style="cyan")
    table.add_column("source", style="magenta")
    table.add_column("pts", justify="right", style="green")
    table.add_column("age", justify="right")
    table.add_column("title")

    now = datetime.now(UTC)
    for item in items:
        if item.published_at is not None:
            hours = (now - item.published_at).total_seconds() / 3600
            age = f"{hours:.0f}h"
        else:
            age = "-"
        table.add_row(
            item.category,
            item.source,
            str(item.points) if item.points is not None else "-",
            age,
            item.title,
        )
    Console().print(table)


@app.command()
def rank(config: str = "config.yaml", category: str | None = None) -> None:
    """Fetch, rank and print the top-N per category (no summaries yet)."""
    cfg = load_config(config)
    categories = [category] if category else None
    items = fetch_all(cfg, categories)
    ranked = rank_items(cfg, items)

    now = datetime.now(UTC)
    console = Console()
    for cat, top in ranked.items():
        if categories is not None and cat not in categories:
            continue
        table = Table(title=f"{cat} — top {len(top)}")
        table.add_column("#", justify="right")
        table.add_column("score", justify="right", style="yellow")
        table.add_column("source", style="magenta")
        table.add_column("pts", justify="right", style="green")
        table.add_column("age", justify="right")
        table.add_column("title")
        for idx, item in enumerate(top, 1):
            if item.published_at is not None:
                age = f"{(now - item.published_at).total_seconds() / 3600:.0f}h"
            else:
                age = "-"
            table.add_row(
                str(idx),
                f"{item.score:.3f}",
                item.source,
                str(item.points) if item.points is not None else "-",
                age,
                item.title,
            )
        console.print(table)


@app.command()
def summarize(config: str = "config.yaml", category: str | None = None) -> None:
    """Fetch, rank and LLM-summarize the top-N per category, then print."""
    cfg = load_config(config)
    categories = [category] if category else None
    items = fetch_all(cfg, categories)
    ranked = rank_items(cfg, items)
    provider = build_provider(cfg.llm)
    summarized = summarize_ranked(provider, ranked)

    console = Console()
    for cat, top in summarized.items():
        if categories is not None and cat not in categories:
            continue
        console.print(f"\n[bold underline]{cat}[/]")
        for idx, item in enumerate(top, 1):
            console.print(f"\n[bold]{idx}. {item.title}[/]  [dim]({item.source})[/]")
            console.print(f"   [blue]{item.url}[/]")
            if item.summary:
                console.print(f"   {item.summary}")
            if item.why:
                console.print(f"   [italic]Why it matters:[/] {item.why}")


def main() -> None:
    load_dotenv()
    app()
