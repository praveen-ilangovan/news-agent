"""Command-line entry point (Typer)."""

# Project specific imports
import typer

# Local imports
from .config import load_config
from .logger import get_logger

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


def main() -> None:
    app()
