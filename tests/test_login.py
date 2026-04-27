import shutil
from pathlib import Path
from unittest.mock import MagicMock

from typer.testing import CliRunner

from lcagents.cli import app

runner = CliRunner()
FIXTURE = Path(__file__).parent / "fixtures" / "fake_project"


def test_login_writes_env_file(tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "p"
    shutil.copytree(FIXTURE, project)
    (project / ".env.example").write_text("OPENAI_API_KEY=\nLANGSMITH_API_KEY=\n")
    monkeypatch.chdir(project)

    answers = iter(["sk-openai", "ls-key"])
    fake_text = MagicMock()
    fake_text.return_value.ask.side_effect = lambda: next(answers)
    monkeypatch.setattr("lcagents.commands.login.questionary.password", fake_text)

    result = runner.invoke(app, ["login"])
    assert result.exit_code == 0
    env = (project / ".env").read_text()
    assert "OPENAI_API_KEY=sk-openai" in env
    assert "LANGSMITH_API_KEY=ls-key" in env


def test_login_status_reports_set_keys(tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "p"
    shutil.copytree(FIXTURE, project)
    (project / ".env.example").write_text("OPENAI_API_KEY=\nLANGSMITH_API_KEY=\n")
    (project / ".env").write_text("OPENAI_API_KEY=set\nLANGSMITH_API_KEY=\n")
    monkeypatch.chdir(project)

    result = runner.invoke(app, ["login", "--status"])
    assert result.exit_code == 0
    assert "OPENAI_API_KEY" in result.stdout
    assert "set" in result.stdout
