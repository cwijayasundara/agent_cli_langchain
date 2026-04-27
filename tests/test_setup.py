from pathlib import Path

from typer.testing import CliRunner

from lcagents.cli import app

runner = CliRunner()


def test_setup_installs_skills_into_detected_agents(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    (home / ".claude").mkdir(parents=True)
    (home / ".codex").mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))

    result = runner.invoke(app, ["setup"])
    assert result.exit_code == 0
    assert "claude-code" in result.stdout
    assert "codex" in result.stdout

    assert (home / ".claude" / "skills" / "lcagents-workflow.md").is_file()
    assert (home / ".codex" / "skills" / "lcagents-workflow.md").is_file()


def test_setup_warns_when_no_agents_detected(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "empty-home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))

    result = runner.invoke(app, ["setup"])
    assert result.exit_code == 0
    assert "No coding agents detected" in result.stdout
