from pathlib import Path

from typer.testing import CliRunner

from lcagents.cli import app

runner = CliRunner()

EXPECTED_FILES = [
    "pyproject.toml",
    ".env.example",
    ".gitignore",
    "README.md",
    "CLAUDE.md",
    "AGENTS.md",
    ".claude/settings.json",
    ".agents/lcagents.toml",
    ".agents/skills/project-overview.md",
    ".agents/skills/editing-the-graph.md",
    ".agents/skills/adding-a-tool.md",
    ".agents/skills/writing-evals.md",
    ".agents/skills/deploying.md",
    "agent/__init__.py",
    "agent/agent.py",
    "agent/graph.py",
    "agent/tools.py",
    "agent/prompts.py",
    "evals/datasets/smoke.jsonl",
    "evals/evaluators.py",
    "evals/run.py",
    "tests/test_agent.py",
    "langgraph.json",
    "server/__init__.py",
    "server/app.py",
    "server/Dockerfile",
]


def test_scaffold_creates_full_layout(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["scaffold", "create", "demo", "--template", "langgraph-agent"])
    assert result.exit_code == 0, result.stdout

    project = tmp_path / "demo"
    for rel in EXPECTED_FILES:
        assert (project / rel).is_file(), f"Missing: {rel}"


def test_scaffold_substitutes_project_name(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["scaffold", "create", "demo", "--template", "langgraph-agent"])
    assert "demo" in (tmp_path / "demo" / "pyproject.toml").read_text()
    assert "demo" in (tmp_path / "demo" / "agent" / "prompts.py").read_text()


def test_scaffold_writes_lcagents_toml(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["scaffold", "create", "demo", "--template", "langgraph-agent"])
    cfg = (tmp_path / "demo" / ".agents" / "lcagents.toml").read_text()
    assert 'template = "langgraph-agent"' in cfg
    assert 'deploy_target = "docker"' in cfg


def test_scaffold_refuses_to_overwrite(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "demo").mkdir()
    result = runner.invoke(app, ["scaffold", "create", "demo", "--template", "langgraph-agent"])
    assert result.exit_code == 1
    assert "Refusing to overwrite" in result.stdout


DEEP_AGENT_FILES = [
    "pyproject.toml",
    "CLAUDE.md",
    ".agents/lcagents.toml",
    ".agents/skills/project-overview.md",
    ".agents/skills/adding-a-subagent.md",
    "agent/agent.py",
    "agent/subagents.py",
    "agent/tools.py",
    "agent/prompts.py",
]


def test_scaffold_deep_agent_template(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["scaffold", "create", "deep", "--template", "deep-agent"])
    assert result.exit_code == 0
    project = tmp_path / "deep"
    for rel in DEEP_AGENT_FILES:
        assert (project / rel).is_file(), f"Missing: {rel}"
    assert "deepagents" in (project / "pyproject.toml").read_text()


def test_scaffold_chain_template(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["scaffold", "create", "rag", "--template", "langchain-chain"])
    assert result.exit_code == 0
    project = tmp_path / "rag"
    for rel in [
        "agent/agent.py",
        "agent/chain.py",
        ".agents/skills/editing-the-chain.md",
        "pyproject.toml",
    ]:
        assert (project / rel).is_file(), f"Missing: {rel}"
