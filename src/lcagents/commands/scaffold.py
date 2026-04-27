"""`lcagents scaffold ...` command group."""
from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from lcagents.config import DeployTarget, Template, find_project_root
from lcagents.scaffold import enhance_project, scaffold_project
from lcagents.upgrade import upgrade_project

console = Console()
app = typer.Typer(help="Scaffold, enhance, or upgrade an lcagents project.")


@app.command("create", help="Create a new project.")
def create(
    name: str = typer.Argument(..., help="Project directory name to create."),
    template: Template = typer.Option(  # noqa: B008
        "langgraph-agent", "--template", "-t", help="Which template to use."
    ),
    deploy_target: DeployTarget = typer.Option(  # noqa: B008
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


@app.command("enhance", help="Add deploy/evals or switch deploy target.")
def enhance(
    add: list[str] = typer.Option([], "--add", help="Subsystem(s) to add: docker, evals."),  # noqa: B008
    target: DeployTarget | None = typer.Option(  # noqa: B008
        None, "--target", help="Switch default deploy target."
    ),
) -> None:
    project = find_project_root(Path.cwd())
    if project is None:
        console.print("[red]No lcagents project found.[/red]")
        raise typer.Exit(1)

    added, already = enhance_project(project, add, target)
    for a in added:
        console.print(f"[green]Added[/green] {a}")
    for a in already:
        console.print(f"[yellow]{a} already present[/yellow]")
    if target:
        console.print(f"[green]Set deploy_target = {target}[/green]")


@app.command("upgrade", help="Re-sync skill files and template content.")
def upgrade() -> None:
    project = find_project_root(Path.cwd())
    if project is None:
        console.print("[red]No lcagents project found.[/red]")
        raise typer.Exit(1)
    updated, conflicts = upgrade_project(project)
    for u in updated:
        console.print(f"[green]Updated[/green] {u.relative_to(project)}")
    for c in conflicts:
        console.print(f"[yellow]Conflict[/yellow] {c.relative_to(project)}")
