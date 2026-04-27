import shutil
from pathlib import Path

from typer.testing import CliRunner

from lcagents.cli import app

runner = CliRunner()


def _scaffold(tmp_path: Path, monkeypatch) -> Path:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["scaffold", "create", "demo", "--template", "langgraph-agent"])
    return tmp_path / "demo"


def test_enhance_add_docker_is_idempotent(tmp_path: Path, monkeypatch) -> None:
    project = _scaffold(tmp_path, monkeypatch)
    monkeypatch.chdir(project)
    result = runner.invoke(app, ["scaffold", "enhance", "--add", "docker"])
    assert result.exit_code == 0
    assert "already present" in result.stdout.lower()


def test_enhance_add_docker_adds_missing(tmp_path: Path, monkeypatch) -> None:
    project = _scaffold(tmp_path, monkeypatch)
    shutil.rmtree(project / "server")
    monkeypatch.chdir(project)

    result = runner.invoke(app, ["scaffold", "enhance", "--add", "docker"])
    assert result.exit_code == 0
    assert (project / "server" / "Dockerfile").is_file()
    assert (project / "server" / "app.py").is_file()


def test_enhance_target_switches_deploy_target(tmp_path: Path, monkeypatch) -> None:
    project = _scaffold(tmp_path, monkeypatch)
    monkeypatch.chdir(project)

    result = runner.invoke(app, ["scaffold", "enhance", "--target", "langsmith"])
    assert result.exit_code == 0

    cfg = (project / ".agents" / "lcagents.toml").read_text()
    assert 'deploy_target = "langsmith"' in cfg
