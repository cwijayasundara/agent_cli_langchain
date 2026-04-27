"""`lcagents run "<prompt>"` — invoke the project's `agent` once."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

import typer
from rich.console import Console

from lcagents.config import find_project_root

console = Console()


def run(prompt: str = typer.Argument(..., help="Prompt to send to the agent.")) -> None:
    """Invoke `agent.agent:agent` once with the given prompt."""
    project_root = find_project_root(Path.cwd())
    if project_root is None:
        console.print("[red]No lcagents project found in this directory.[/red]")
        raise typer.Exit(1)

    sys.path.insert(0, str(project_root))
    try:
        module = importlib.import_module("agent.agent")
    except ImportError as exc:
        console.print(f"[red]Could not import agent.agent:[/red] {exc}")
        raise typer.Exit(1) from None

    agent_obj = getattr(module, "agent", None)
    if agent_obj is None or not hasattr(agent_obj, "invoke"):
        console.print("[red]agent.agent must export `agent` with an .invoke() method.[/red]")
        raise typer.Exit(1)

    result = agent_obj.invoke({"messages": [{"role": "user", "content": prompt}]})
    _print_result(result)


def _print_result(result: object) -> None:
    if isinstance(result, dict) and "messages" in result:
        msgs = result["messages"]
        if msgs:
            last = msgs[-1]
            if isinstance(last, dict):
                console.print(last.get("content", ""))
            else:
                console.print(getattr(last, "content", str(last)))
            return
    console.print(str(result))
