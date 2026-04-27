"""`lcagents eval run` and `lcagents eval compare`.

Module name is plural (`evals`) to avoid shadowing Python's built-in `eval`.
The user-facing CLI subcommand is singular: `lcagents eval ...`.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from lcagents.config import find_project_root

console = Console()
app = typer.Typer(help="Run and compare LangSmith evals.")


@app.command("run")
def run_cmd(smoke: bool = typer.Option(False, "--smoke", help="Run only smoke dataset.")) -> None:
    """Run the project's evals/run.py."""
    project = find_project_root(Path.cwd())
    if project is None:
        console.print("[red]No lcagents project found.[/red]")
        raise typer.Exit(1)
    if not os.getenv("LANGSMITH_API_KEY"):
        console.print("[red]LANGSMITH_API_KEY is not set. Run `lcagents login`.[/red]")
        raise typer.Exit(2)

    cmd = [sys.executable, str(project / "evals" / "run.py")]
    if smoke:
        cmd.append("--smoke")
    proc = subprocess.run(cmd, cwd=project)
    raise typer.Exit(proc.returncode)


@app.command("compare")
def compare_cmd(a: Path, b: Path) -> None:
    """Diff two eval result JSON files."""
    da = json.loads(a.read_text("utf-8"))
    db = json.loads(b.read_text("utf-8"))

    table = Table(title=f"{a.name}  ->  {b.name}")
    table.add_column("dataset")
    table.add_column("metric")
    table.add_column(a.name)
    table.add_column(b.name)
    table.add_column("delta")

    for ds in sorted(set(da) | set(db)):
        scores_a = {r["key"]: r["score"] for r in da.get(ds, [])}
        scores_b = {r["key"]: r["score"] for r in db.get(ds, [])}
        for key in sorted(set(scores_a) | set(scores_b)):
            sa = scores_a.get(key)
            sb = scores_b.get(key)
            delta = (sb - sa) if (sa is not None and sb is not None) else None
            delta_str = f"{delta:+.2f}" if delta is not None else "-"
            table.add_row(ds, key, _fmt(sa), _fmt(sb), delta_str)

    console.print(table)


def _fmt(v: float | None) -> str:
    return "-" if v is None else f"{v:.2f}"
