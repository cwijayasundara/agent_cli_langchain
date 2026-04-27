"""`lcagents install` — uv sync in the project root."""
from __future__ import annotations

import subprocess
from pathlib import Path

import typer
from rich.console import Console

from lcagents.config import find_project_root

console = Console()


def install() -> None:
    project = find_project_root(Path.cwd())
    if project is None:
        console.print("[red]No lcagents project found.[/red]")
        raise typer.Exit(1)
    proc = subprocess.run(["uv", "sync"], cwd=project)
    raise typer.Exit(proc.returncode)
