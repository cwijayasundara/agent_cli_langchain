"""`lcagents scaffold ...` command group."""
from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from lcagents.config import DeployTarget, Template
from lcagents.scaffold import scaffold_project

console = Console()
app = typer.Typer(help="Scaffold, enhance, or upgrade an lcagents project.")


@app.command("create", help="Create a new project.")
def create(
    name: str = typer.Argument(..., help="Project directory name to create."),
    template: Template = typer.Option(
        "langgraph-agent", "--template", "-t", help="Which template to use."
    ),
    deploy_target: DeployTarget = typer.Option(
        "docker", "--deploy-target", help="Default deploy target written into lcagents.toml."
    ),
) -> None:
    try:
        root = scaffold_project(name, template, deploy_target, Path.cwd())
    except FileExistsError as exc:
        console.print(f"[red]Refusing to overwrite existing path:[/red] {exc}")
        raise typer.Exit(1) from None

    console.print(f"[green]Scaffolded[/green] {root}")
    console.print(f"  Template: {template}")
    console.print(f"  Deploy target: {deploy_target}")
    console.print("\nNext steps:")
    console.print(f"  cd {name}")
    console.print("  lcagents install")
    console.print("  cp .env.example .env  # then fill in keys")
    console.print('  lcagents run "hello"')
