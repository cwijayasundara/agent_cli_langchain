import shutil
from pathlib import Path
from unittest.mock import MagicMock

from typer.testing import CliRunner

from lcagents.cli import app

runner = CliRunner()
FIXTURE_PROJECT = Path(__file__).parent / "fixtures" / "fake_project"
FIXTURE_RESULTS = Path(__file__).parent / "fixtures" / "eval_results"


def test_eval_run_invokes_evals_run_py(tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "p"
    shutil.copytree(FIXTURE_PROJECT, project)
    (project / "evals").mkdir()
    (project / "evals" / "run.py").write_text("import sys; sys.exit(0)\n")
    monkeypatch.chdir(project)
    monkeypatch.setenv("LANGSMITH_API_KEY", "fake")

    fake = MagicMock(return_value=MagicMock(returncode=0))
    monkeypatch.setattr("lcagents.commands.evals.subprocess.run", fake)

    result = runner.invoke(app, ["eval", "run"])
    assert result.exit_code == 0
    args = fake.call_args.args[0]
    assert args[-1].endswith("evals/run.py") or args[-1].endswith("evals\\run.py")


def test_eval_run_fails_without_langsmith_key(tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "p"
    shutil.copytree(FIXTURE_PROJECT, project)
    (project / "evals").mkdir()
    (project / "evals" / "run.py").write_text("")
    monkeypatch.chdir(project)
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)

    result = runner.invoke(app, ["eval", "run"])
    assert result.exit_code == 2
    assert "LANGSMITH_API_KEY" in result.stdout


def test_eval_compare_prints_deltas() -> None:
    result = runner.invoke(app, [
        "eval", "compare",
        str(FIXTURE_RESULTS / "a.json"),
        str(FIXTURE_RESULTS / "b.json"),
    ])
    assert result.exit_code == 0
    assert "correctness" in result.stdout
    assert "+0.10" in result.stdout
    assert "latency" in result.stdout
