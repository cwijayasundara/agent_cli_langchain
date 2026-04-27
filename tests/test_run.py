import shutil
from pathlib import Path

from typer.testing import CliRunner

from lcagents.cli import app

runner = CliRunner()
FIXTURE = Path(__file__).parent / "fixtures" / "fake_project"


def test_run_invokes_agent_and_prints_response(tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "proj"
    shutil.copytree(FIXTURE, project)
    monkeypatch.chdir(project)

    result = runner.invoke(app, ["run", "hello world"])
    assert result.exit_code == 0
    assert "echo: hello world" in result.stdout


def test_run_fails_outside_project(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["run", "hi"])
    assert result.exit_code == 1
    assert "No lcagents project" in result.stdout
