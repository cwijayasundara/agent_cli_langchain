"""`lcagents lint` — ruff + mypy."""
from __future__ import annotations

import subprocess
from pathlib import Path

import typer
from rich.console import Console

from lcagents.config import find_project_root

console = Console()


def lint(quiet: bool = typer.Option(False, "--quiet", help="Suppress non-error output.")) -> None:
    project = find_project_root(Path.cwd())
    if project is None:
        console.print("[red]No lcagents project found.[/red]")
        raise typer.Exit(1)

    stdout = subprocess.DEVNULL if quiet else None
    ruff = subprocess.run(["ruff", "check", "."], cwd=project, stdout=stdout)
    mypy = subprocess.run(["mypy", "agent"], cwd=project, stdout=stdout)
    raise typer.Exit(max(ruff.returncode, mypy.returncode))
