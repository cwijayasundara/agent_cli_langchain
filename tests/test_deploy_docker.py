import shutil
from pathlib import Path
from unittest.mock import MagicMock

from typer.testing import CliRunner

from lcagents.cli import app

runner = CliRunner()
FIXTURE = Path(__file__).parent / "fixtures" / "fake_project"


def _setup(tmp_path: Path, monkeypatch) -> Path:
    project = tmp_path / "p"
    shutil.copytree(FIXTURE, project)
    (project / "evals").mkdir()
    (project / "evals" / "run.py").write_text("import sys; sys.exit(0)\n")
    monkeypatch.chdir(project)
    monkeypatch.setenv("LANGSMITH_API_KEY", "fake")
    return project


def test_deploy_docker_runs_smoke_then_builds(tmp_path: Path, monkeypatch) -> None:
    _setup(tmp_path, monkeypatch)

    smoke_run = MagicMock(return_value=MagicMock(returncode=0))
    monkeypatch.setattr("lcagents.commands.deploy.subprocess.run", smoke_run)

    fake_client = MagicMock()
    fake_client.images.build.return_value = (MagicMock(id="sha256:abc"), iter([]))
    fake_container = MagicMock()
    fake_container.attrs = {"NetworkSettings": {"Ports": {"8080/tcp": [{"HostPort": "55555"}]}}}
    fake_client.containers.run.return_value = fake_container
    monkeypatch.setattr("lcagents.commands.deploy.docker.from_env", lambda: fake_client)

    fake_post = MagicMock(return_value=MagicMock(status_code=200))
    monkeypatch.setattr("lcagents.commands.deploy.httpx.post", fake_post)

    result = runner.invoke(app, ["deploy", "docker", "--tag", "demo:latest"])
    assert result.exit_code == 0, result.stdout
    smoke_run.assert_called_once()
    fake_client.images.build.assert_called_once()
    fake_container.stop.assert_called_once()


def test_deploy_docker_aborts_on_smoke_failure(tmp_path: Path, monkeypatch) -> None:
    _setup(tmp_path, monkeypatch)
    smoke_run = MagicMock(return_value=MagicMock(returncode=1))
    monkeypatch.setattr("lcagents.commands.deploy.subprocess.run", smoke_run)

    result = runner.invoke(app, ["deploy", "docker", "--tag", "demo:latest"])
    assert result.exit_code == 1
    assert "smoke" in result.stdout.lower()
