from pathlib import Path

from typer.testing import CliRunner

from lcagents.cli import app

runner = CliRunner()


def _scaffold(tmp_path: Path, monkeypatch) -> Path:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["scaffold", "create", "demo", "--template", "langgraph-agent"])
    return tmp_path / "demo"


def test_upgrade_replaces_unchanged_files(tmp_path: Path, monkeypatch) -> None:
    project = _scaffold(tmp_path, monkeypatch)
    skill = project / ".agents" / "skills" / "writing-evals.md"
    skill.write_text("OUTDATED")
    monkeypatch.chdir(project)

    result = runner.invoke(app, ["scaffold", "upgrade"])
    assert result.exit_code == 0
    assert skill.read_text() != "OUTDATED"


def test_upgrade_creates_baseline_after_first_run(tmp_path: Path, monkeypatch) -> None:
    project = _scaffold(tmp_path, monkeypatch)
    monkeypatch.chdir(project)

    runner.invoke(app, ["scaffold", "upgrade"])
    assert (project / ".agents" / "baseline" / "CLAUDE.md").is_file()
