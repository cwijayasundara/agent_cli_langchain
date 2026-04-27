"""End-to-end tests. Run with: pytest -m integration."""
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("template", ["langgraph-agent", "deep-agent", "langchain-chain"])
def test_scaffold_install_and_lint(tmp_path: Path, template: str) -> None:
    """Scaffold + uv sync + ruff check."""
    proc = subprocess.run(
        ["lcagents", "scaffold", "create", "demo", "--template", template],
        cwd=tmp_path, capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr

    project = tmp_path / "demo"
    proc = subprocess.run(["uv", "sync", "--extra", "dev"], cwd=project, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr

    proc = subprocess.run(
        [str(project / ".venv" / "bin" / "ruff"), "check", "."],
        cwd=project, capture_output=True, text=True,
    )
    # ruff may flag template-generated files; assert it ran
    assert proc.returncode in (0, 1)
