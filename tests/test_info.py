from typer.testing import CliRunner

from lcagents.cli import app

runner = CliRunner()


def test_info_prints_version() -> None:
    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0
    assert "lcagents" in result.stdout
    assert "0.1.0" in result.stdout


def test_info_shows_no_project_when_outside_project(tmp_project, monkeypatch) -> None:
    monkeypatch.chdir(tmp_project)
    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0
    assert "No lcagents project detected" in result.stdout
