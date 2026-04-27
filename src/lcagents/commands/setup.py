"""`lcagents setup` — install global skills into detected coding agents."""
from __future__ import annotations

from importlib.resources import files
from pathlib import Path

import typer
from rich.console import Console

from lcagents.coding_agents import detect_coding_agents, install_skills

console = Console()


def setup(force: bool = typer.Option(False, "--force", help="Reinstall even if already present.")) -> None:
    """Install lcagents skills into Claude Code, Codex, etc."""
    _ = force  # install_skills already overwrites; flag reserved for future per-file checks
    agents = detect_coding_agents()
    if not agents:
        console.print("[yellow]No coding agents detected[/yellow] (looked for ~/.claude, ~/.codex).")
        raise typer.Exit(0)

    skills_dir = Path(str(files("lcagents") / "skills"))
    install_skills(agents, skills_dir)
    for agent in agents:
        console.print(f"[green]Installed skills into {agent.name}[/green] ({agent.skills_dir})")
