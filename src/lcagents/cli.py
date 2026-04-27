"""Top-level Typer app for lcagents."""
from __future__ import annotations

import typer

from lcagents.commands import info as info_cmd
from lcagents.commands import run as run_cmd
from lcagents.commands import scaffold as scaffold_cmd
from lcagents.commands import setup as setup_cmd

app = typer.Typer(
    name="lcagents",
    help="A tool for coding agents to scaffold/run/evaluate/deploy LangChain projects.",
    no_args_is_help=True,
)


@app.callback(invoke_without_command=True)
def _main(ctx: typer.Context) -> None:
    """lcagents — LangChain project toolkit."""


app.command("info")(info_cmd.info)
app.command("setup")(setup_cmd.setup)
app.command("run")(run_cmd.run)
app.add_typer(scaffold_cmd.app, name="scaffold")
