import shutil
from pathlib import Path
from unittest.mock import MagicMock

from typer.testing import CliRunner

from lcagents.cli import app

runner = CliRunner()
FIXTURE = Path(__file__).parent / "fixtures" / "fake_project"


def _setup_project(tmp_path: Path, monkeypatch) -> Path:
    project = tmp_path / "proj"
    shutil.copytree(FIXTURE, project)
    monkeypatch.chdir(project)
    return project


def test_install_runs_uv_sync(tmp_path: Path, monkeypatch) -> None:
    _setup_project(tmp_path, monkeypatch)
    fake_run = MagicMock(return_value=MagicMock(returncode=0))
    monkeypatch.setattr("lcagents.commands.install.subprocess.run", fake_run)

    result = runner.invoke(app, ["install"])
    assert result.exit_code == 0
    fake_run.assert_called_once()
    assert fake_run.call_args.args[0][:2] == ["uv", "sync"]


def test_lint_runs_ruff_and_mypy(tmp_path: Path, monkeypatch) -> None:
    _setup_project(tmp_path, monkeypatch)
    fake_run = MagicMock(return_value=MagicMock(returncode=0))
    monkeypatch.setattr("lcagents.commands.lint.subprocess.run", fake_run)

    result = runner.invoke(app, ["lint"])
    assert result.exit_code == 0
    assert fake_run.call_count == 2
    cmds = [call.args[0][0] for call in fake_run.call_args_list]
    assert "ruff" in cmds
    assert "mypy" in cmds


def test_dev_delegates_to_langgraph(tmp_path: Path, monkeypatch) -> None:
    _setup_project(tmp_path, monkeypatch)
    fake_run = MagicMock(return_value=MagicMock(returncode=0))
    monkeypatch.setattr("lcagents.commands.dev.subprocess.run", fake_run)

    result = runner.invoke(app, ["dev"])
    assert result.exit_code == 0
    fake_run.assert_called_once()
    assert fake_run.call_args.args[0][:2] == ["langgraph", "dev"]


def test_lint_quiet_suppresses_output(tmp_path: Path, monkeypatch) -> None:
    _setup_project(tmp_path, monkeypatch)
    fake_run = MagicMock(return_value=MagicMock(returncode=0))
    monkeypatch.setattr("lcagents.commands.lint.subprocess.run", fake_run)

    result = runner.invoke(app, ["lint", "--quiet"])
    assert result.exit_code == 0
