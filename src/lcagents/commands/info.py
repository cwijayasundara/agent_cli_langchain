"""`lcagents info` — show CLI version and project status."""
from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from lcagents import __version__

console = Console()


def info() -> None:
    """Show CLI version, project config, and detected coding agents."""
    console.print(f"[bold]lcagents[/bold] version [cyan]{__version__}[/cyan]")

    project_root = _find_project_root(Path.cwd())
    if project_root is None:
        console.print("No lcagents project detected in the current directory.")
        raise typer.Exit(0)

    console.print(f"Project root: [green]{project_root}[/green]")


def _find_project_root(start: Path) -> Path | None:
    for d in (start, *start.parents):
        if (d / ".agents" / "lcagents.toml").is_file():
            return d
    return None
