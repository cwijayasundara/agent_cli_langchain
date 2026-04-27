"""`lcagents login` — populate .env from .env.example interactively."""
from __future__ import annotations

from pathlib import Path

import questionary
import typer
from rich.console import Console

from lcagents.config import find_project_root

console = Console()


def login(status: bool = typer.Option(False, "--status", help="Show which keys are set.")) -> None:
    project = find_project_root(Path.cwd())
    if project is None:
        console.print("[red]No lcagents project found.[/red]")
        raise typer.Exit(1)

    env_path = project / ".env"
    example_path = project / ".env.example"

    if status:
        existing = _parse_env(env_path) if env_path.exists() else {}
        for key in _keys_from_example(example_path):
            mark = "set" if existing.get(key) else "[yellow]missing[/yellow]"
            console.print(f"  {key}: {mark}")
        return

    keys = _keys_from_example(example_path)
    existing = _parse_env(env_path) if env_path.exists() else {}
    for key in keys:
        if existing.get(key):
            continue
        value = questionary.password(f"{key}:").ask()
        if value:
            existing[key] = value

    env_path.write_text("\n".join(f"{k}={v}" for k, v in existing.items()) + "\n")
    console.print(f"[green]Wrote[/green] {env_path}")


def _keys_from_example(path: Path) -> list[str]:
    keys: list[str] = []
    if not path.exists():
        return keys
    for raw in path.read_text("utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        keys.append(line.split("=", 1)[0])
    return keys


def _parse_env(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in path.read_text("utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k] = v
    return out
