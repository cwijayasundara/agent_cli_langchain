"""`lcagents deploy {langsmith,docker}`."""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import docker
import httpx
import typer
from rich.console import Console

from lcagents.config import find_project_root

console = Console()
app = typer.Typer(help="Deploy the agent.")


def _smoke_check(project: Path) -> int:
    """Run the smoke dataset as a deploy gate."""
    if not os.getenv("LANGSMITH_API_KEY"):
        console.print("[red]LANGSMITH_API_KEY required for the smoke pre-flight.[/red]")
        return 2
    proc = subprocess.run(
        [sys.executable, str(project / "evals" / "run.py"), "--smoke"],
        cwd=project,
    )
    return proc.returncode


@app.command("docker")
def docker_deploy(
    tag: str = typer.Option(..., "--tag", help="Image tag, e.g. my-agent:latest"),
    push: str | None = typer.Option(None, "--push", help="Optional registry to push to"),
) -> None:
    project = find_project_root(Path.cwd())
    if project is None:
        console.print("[red]No lcagents project found.[/red]")
        raise typer.Exit(1)

    console.print("[bold]Pre-flight: smoke check[/bold]")
    rc = _smoke_check(project)
    if rc != 0:
        console.print("[red]Smoke check failed; refusing to build.[/red]")
        raise typer.Exit(1)

    client = docker.from_env()
    console.print(f"[bold]Building image[/bold] {tag}")
    image, _logs = client.images.build(
        path=str(project), dockerfile="server/Dockerfile", tag=tag, rm=True
    )
    console.print(f"[green]Built[/green] {image.id}")

    if push:
        full = f"{push}/{tag}"
        client.images.get(tag).tag(full)
        client.images.push(full)
        console.print(f"[green]Pushed[/green] {full}")

    console.print("[bold]Smoke-testing the container[/bold]")
    container = client.containers.run(tag, detach=True, ports={"8080/tcp": None}, environment={})
    try:
        container.reload()
        port = container.attrs["NetworkSettings"]["Ports"]["8080/tcp"][0]["HostPort"]
        time.sleep(2)
        resp = httpx.post(
            f"http://localhost:{port}/invoke",
            json={"input": {"messages": [{"role": "user", "content": "hello"}]}},
            timeout=30,
        )
        if resp.status_code != 200:
            console.print(f"[red]Container responded with {resp.status_code}[/red]")
            raise typer.Exit(1)
        console.print(f"[green]Container OK[/green] (port {port})")
    finally:
        container.stop()
        container.remove()

    console.print(f"\nRun it: [bold]docker run --env-file .env -p 8080:8080 {tag}[/bold]")


@app.command("langsmith")
def langsmith_deploy() -> None:
    project = find_project_root(Path.cwd())
    if project is None:
        console.print("[red]No lcagents project found.[/red]")
        raise typer.Exit(1)

    console.print("[bold]Pre-flight: smoke check[/bold]")
    if _smoke_check(project) != 0:
        console.print("[red]Smoke check failed; refusing to deploy.[/red]")
        raise typer.Exit(1)

    console.print("[bold]Building with langgraph[/bold]")
    rc = subprocess.run(["langgraph", "build", "-t", project.name], cwd=project).returncode
    if rc != 0:
        raise typer.Exit(rc)

    rc = subprocess.run(["langgraph", "deploy"], cwd=project).returncode
    raise typer.Exit(rc)
