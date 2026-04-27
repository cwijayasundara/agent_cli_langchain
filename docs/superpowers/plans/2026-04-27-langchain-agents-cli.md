# `langchain-agents-cli` (`lcagents`) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `lcagents` Python CLI plus its skill bundle, scaffolding three LangChain-ecosystem project templates with a single canonical layout, and supporting headless run, LangSmith evals, and two deploy targets (LangSmith Cloud, Docker).

**Architecture:** Single Python package (`src/lcagents/`) exposing a Typer CLI. Templates rendered with Jinja2 from `templates/` (one dir per template plus `_shared/`). Global skill `.md` files in `skills/` shipped to coding agents by `setup`. Project-local skills in `project_skills/` copied at scaffold time. CLI does not depend on `langchain`/`langgraph`/`deepagents` at runtime — those are deps of the *scaffolded* projects.

**Tech Stack:** Python 3.11+, Typer, Jinja2, questionary, httpx, docker SDK, stdlib `tomllib` + `tomli_w`, pytest, pytest-docker, hatchling build backend, `uv` for dev environment.

**Reference spec:** `docs/superpowers/specs/2026-04-27-langchain-agents-cli-design.md` — read this before starting any task.

**Naming note:** the user-facing CLI subcommand is `lcagents eval ...` to match the design spec, but inside the codebase the Python module is `commands/evals.py` (plural) to avoid shadowing Python's built-in `eval` and to keep static-analysis tooling happy. The LangSmith evaluation function is imported under an alias (`run_evaluation`).

**Plan size note:** ~20 tasks. Tasks 1–9 produce a CLI that can scaffold and run a `langgraph-agent` project end-to-end. Tasks 10–14 add the other two templates + dev/evals. Tasks 15–19 add deploy + lifecycle commands + skill content + integration tests. The plan is sequenced so the system is exercisable as early as possible.

---

## Task 0: Repo bootstrap

**Files:**
- Create: `.gitignore`
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `src/lcagents/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 0.1: Initialize git**

```bash
cd /Users/chamindawijayasundara/Documents/rnd_2026/agent_cli_langchain
git init
git config user.email "cwijay@biz2bricks.ai"
git config user.name "Chaminda Wijayasundara"
```

- [ ] **Step 0.2: Write `.gitignore`**

```
__pycache__/
*.py[cod]
.venv/
.env
.pytest_cache/
.ruff_cache/
.mypy_cache/
dist/
build/
*.egg-info/
.coverage
htmlcov/
```

- [ ] **Step 0.3: Write `pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "langchain-agents-cli"
version = "0.1.0"
description = "A tool for coding agents to scaffold, run, evaluate, and deploy LangChain / LangGraph / DeepAgents projects."
readme = "README.md"
requires-python = ">=3.11"
authors = [{name = "Chaminda Wijayasundara", email = "cwijay@biz2bricks.ai"}]
license = "Apache-2.0"
dependencies = [
    "typer>=0.12",
    "jinja2>=3.1",
    "questionary>=2.0",
    "httpx>=0.27",
    "tomli-w>=1.0",
    "docker>=7.0",
    "rich>=13.7",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-docker>=3.1",
    "pytest-mock>=3.12",
    "ruff>=0.5",
    "mypy>=1.10",
]

[project.scripts]
lcagents = "lcagents.cli:app"

[tool.hatch.build.targets.wheel]
packages = ["src/lcagents"]

[tool.hatch.build.targets.wheel.force-include]
"src/lcagents/templates" = "lcagents/templates"
"src/lcagents/skills" = "lcagents/skills"
"src/lcagents/project_skills" = "lcagents/project_skills"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "B", "SIM"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v"
```

- [ ] **Step 0.4: Write `README.md` (placeholder; final version in Task 19)**

```markdown
# langchain-agents-cli (`lcagents`)

A tool *for* coding agents (Claude Code, Codex), not a coding agent itself. Scaffolds, runs, evaluates, and deploys LangChain / LangGraph / DeepAgents projects.

See `docs/superpowers/specs/2026-04-27-langchain-agents-cli-design.md` for the design.

## Install (dev)

    uv venv
    uv pip install -e ".[dev]"

## Run tests

    pytest
```

- [ ] **Step 0.5: Write `src/lcagents/__init__.py`**

```python
__version__ = "0.1.0"
```

- [ ] **Step 0.6: Write `tests/__init__.py` (empty) and `tests/conftest.py`**

`tests/conftest.py`:
```python
"""Shared pytest fixtures."""
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """A clean tmp dir to act as a scaffolded project root."""
    return tmp_path
```

- [ ] **Step 0.7: Install dev deps and verify pytest runs**

```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
pytest
```
Expected: clean collection (exit 5 / "no tests ran" is fine).

- [ ] **Step 0.8: Commit**

```bash
git add .
git commit -m "chore: bootstrap repo (pyproject, gitignore, package skeleton)"
```

---

## Task 1: CLI entry point + `info` command

The smallest end-to-end slice.

**Files:**
- Create: `src/lcagents/cli.py`
- Create: `src/lcagents/__main__.py`
- Create: `src/lcagents/commands/__init__.py`
- Create: `src/lcagents/commands/info.py`
- Create: `tests/test_info.py`

- [ ] **Step 1.1: Write the failing test**

`tests/test_info.py`:
```python
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
```

- [ ] **Step 1.2: Run to verify failure**

```bash
pytest tests/test_info.py -v
```
Expected: ImportError on `lcagents.cli`.

- [ ] **Step 1.3: Implement `src/lcagents/cli.py`**

```python
"""Top-level Typer app for lcagents."""
from __future__ import annotations

import typer

from lcagents.commands import info as info_cmd

app = typer.Typer(
    name="lcagents",
    help="A tool for coding agents to scaffold/run/evaluate/deploy LangChain projects.",
    no_args_is_help=True,
)

app.command("info")(info_cmd.info)
```

- [ ] **Step 1.4: Implement `src/lcagents/__main__.py`**

```python
from lcagents.cli import app

if __name__ == "__main__":
    app()
```

- [ ] **Step 1.5: Implement `src/lcagents/commands/__init__.py`** — empty file.

- [ ] **Step 1.6: Implement `src/lcagents/commands/info.py`**

```python
"""`lcagents info` — show CLI version and project status."""
from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from lcagents import __version__

console = Console()


def info() -> None:
    """Show CLI version, project config, and detected coding agents."""
    console.print(f"[bold]lcagents[/bold] version [cyan]{__version__}[/cyan]")

    project_root = _find_project_root(Path.cwd())
    if project_root is None:
        console.print("No lcagents project detected in the current directory.")
        raise typer.Exit(0)

    console.print(f"Project root: [green]{project_root}[/green]")


def _find_project_root(start: Path) -> Path | None:
    for d in (start, *start.parents):
        if (d / ".agents" / "lcagents.toml").is_file():
            return d
    return None
```

- [ ] **Step 1.7: Run tests to verify pass**

```bash
pytest tests/test_info.py -v
```
Expected: 2 passed.

- [ ] **Step 1.8: Smoke-test the binary**

```bash
lcagents info
```
Expected: includes `lcagents version 0.1.0` and `No lcagents project detected`.

- [ ] **Step 1.9: Commit**

```bash
git add src/lcagents tests/test_info.py
git commit -m "feat(cli): add Typer entry point and info command"
```

---

## Task 2: Project config module (`.agents/lcagents.toml`)

**Files:**
- Create: `src/lcagents/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 2.1: Write the failing test**

`tests/test_config.py`:
```python
from pathlib import Path

import pytest

from lcagents.config import LcAgentsConfig, find_project_root, load_config, save_config


def test_save_and_load_roundtrip(tmp_project: Path) -> None:
    cfg = LcAgentsConfig(
        template="langgraph-agent",
        scaffolder_version="0.1.0",
        deploy_target="docker",
    )
    save_config(tmp_project, cfg)
    assert load_config(tmp_project) == cfg


def test_find_project_root_walks_up(tmp_project: Path) -> None:
    save_config(tmp_project, LcAgentsConfig("deep-agent", "0.1.0", "langsmith"))
    nested = tmp_project / "agent" / "tools"
    nested.mkdir(parents=True)
    assert find_project_root(nested) == tmp_project


def test_find_project_root_returns_none_when_missing(tmp_project: Path) -> None:
    assert find_project_root(tmp_project) is None


def test_load_config_raises_when_missing(tmp_project: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_config(tmp_project)
```

- [ ] **Step 2.2: Run to verify failure**

```bash
pytest tests/test_config.py -v
```
Expected: ImportError.

- [ ] **Step 2.3: Implement `src/lcagents/config.py`**

```python
"""Read/write the project's `.agents/lcagents.toml`."""
from __future__ import annotations

import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

import tomli_w

CONFIG_REL_PATH = Path(".agents") / "lcagents.toml"

Template = Literal["langgraph-agent", "deep-agent", "langchain-chain"]
DeployTarget = Literal["langsmith", "docker"]


@dataclass(frozen=True)
class LcAgentsConfig:
    template: Template
    scaffolder_version: str
    deploy_target: DeployTarget


def save_config(project_root: Path, cfg: LcAgentsConfig) -> None:
    path = project_root / CONFIG_REL_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(tomli_w.dumps(asdict(cfg)).encode("utf-8"))


def load_config(project_root: Path) -> LcAgentsConfig:
    path = project_root / CONFIG_REL_PATH
    if not path.is_file():
        raise FileNotFoundError(f"No lcagents project at {project_root}")
    data = tomllib.loads(path.read_text("utf-8"))
    return LcAgentsConfig(**data)


def find_project_root(start: Path) -> Path | None:
    for d in (start, *start.parents):
        if (d / CONFIG_REL_PATH).is_file():
            return d
    return None
```

- [ ] **Step 2.4: Refactor `info.py` to use the shared helper**

In `src/lcagents/commands/info.py`, delete the local `_find_project_root` and replace the call with `from lcagents.config import find_project_root` + `find_project_root(Path.cwd())`.

- [ ] **Step 2.5: Run tests**

```bash
pytest -v
```
Expected: all green.

- [ ] **Step 2.6: Commit**

```bash
git add src/lcagents/config.py src/lcagents/commands/info.py tests/test_config.py
git commit -m "feat(config): add LcAgentsConfig read/write + project root discovery"
```

---

## Task 3: Coding agent detection + skill installation helper

**Files:**
- Create: `src/lcagents/coding_agents.py`
- Create: `tests/test_coding_agents.py`

- [ ] **Step 3.1: Write the failing test**

`tests/test_coding_agents.py`:
```python
from pathlib import Path

from lcagents.coding_agents import CodingAgent, detect_coding_agents, install_skills


def test_detect_finds_claude_code(tmp_path: Path) -> None:
    home = tmp_path / "home"
    (home / ".claude").mkdir(parents=True)
    found = detect_coding_agents(home=home)
    assert any(a.name == "claude-code" for a in found)


def test_detect_finds_codex(tmp_path: Path) -> None:
    home = tmp_path / "home"
    (home / ".codex").mkdir(parents=True)
    found = detect_coding_agents(home=home)
    assert any(a.name == "codex" for a in found)


def test_detect_returns_empty_when_none_installed(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    assert detect_coding_agents(home=home) == []


def test_install_skills_writes_files(tmp_path: Path) -> None:
    home = tmp_path / "home"
    (home / ".claude").mkdir(parents=True)
    skills_src = tmp_path / "skills"
    skills_src.mkdir()
    (skills_src / "lcagents-workflow.md").write_text("# workflow")

    install_skills(detect_coding_agents(home=home), skills_src)

    installed = home / ".claude" / "skills" / "lcagents-workflow.md"
    assert installed.is_file()
    assert installed.read_text() == "# workflow"


def test_install_skills_overwrites_existing(tmp_path: Path) -> None:
    home = tmp_path / "home"
    (home / ".claude" / "skills").mkdir(parents=True)
    (home / ".claude" / "skills" / "lcagents-workflow.md").write_text("OLD")
    skills_src = tmp_path / "skills"
    skills_src.mkdir()
    (skills_src / "lcagents-workflow.md").write_text("NEW")

    install_skills(detect_coding_agents(home=home), skills_src)
    assert (home / ".claude" / "skills" / "lcagents-workflow.md").read_text() == "NEW"
```

- [ ] **Step 3.2: Run to verify failure**

```bash
pytest tests/test_coding_agents.py -v
```
Expected: ImportError.

- [ ] **Step 3.3: Implement `src/lcagents/coding_agents.py`**

```python
"""Detect installed coding agents (Claude Code, Codex) and install lcagents skill files."""
from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

KNOWN_AGENTS = [
    ("claude-code", ".claude"),
    ("codex", ".codex"),
]


@dataclass(frozen=True)
class CodingAgent:
    name: str
    home_dir: Path

    @property
    def skills_dir(self) -> Path:
        return self.home_dir / "skills"


def detect_coding_agents(home: Path | None = None) -> list[CodingAgent]:
    home = home or Path.home()
    found: list[CodingAgent] = []
    for name, rel in KNOWN_AGENTS:
        agent_home = home / rel
        if agent_home.is_dir():
            found.append(CodingAgent(name=name, home_dir=agent_home))
    return found


def install_skills(agents: list[CodingAgent], source: Path) -> None:
    skill_files = sorted(source.glob("*.md"))
    for agent in agents:
        agent.skills_dir.mkdir(parents=True, exist_ok=True)
        for src in skill_files:
            shutil.copy2(src, agent.skills_dir / src.name)
```

- [ ] **Step 3.4: Run tests**

```bash
pytest -v
```
Expected: all green.

- [ ] **Step 3.5: Commit**

```bash
git add src/lcagents/coding_agents.py tests/test_coding_agents.py
git commit -m "feat(setup): add coding-agent detection and skill installation"
```

---

## Task 4: `setup` command + first global skill stub

**Files:**
- Create: `src/lcagents/skills/lcagents-workflow.md`
- Create: `src/lcagents/commands/setup.py`
- Modify: `src/lcagents/cli.py`
- Create: `tests/test_setup.py`

- [ ] **Step 4.1: Write the failing test**

`tests/test_setup.py`:
```python
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
```

- [ ] **Step 4.2: Author the placeholder skill (real content in Task 17)**

`src/lcagents/skills/lcagents-workflow.md`:
```markdown
---
name: lcagents-workflow
description: Use when working in or scaffolding a LangChain agent project with lcagents. Explains the develop -> evals -> deploy lifecycle.
---

# lcagents Workflow

This skill teaches a coding agent the `lcagents` development lifecycle.

(Authoring deferred to Task 17. This stub exists so the install pipeline has content to copy.)
```

- [ ] **Step 4.3: Implement `src/lcagents/commands/setup.py`**

```python
"""`lcagents setup` — install global skills into detected coding agents."""
from __future__ import annotations

from importlib.resources import files
from pathlib import Path

import typer
from rich.console import Console

from lcagents.coding_agents import detect_coding_agents, install_skills

console = Console()


def setup(force: bool = typer.Option(False, "--force", help="Reinstall even if already present.")) -> None:
    """Install lcagents skills into Claude Code, Codex, etc."""
    _ = force  # install_skills already overwrites; flag reserved for future per-file checks
    agents = detect_coding_agents()
    if not agents:
        console.print("[yellow]No coding agents detected[/yellow] (looked for ~/.claude, ~/.codex).")
        raise typer.Exit(0)

    skills_dir = Path(str(files("lcagents") / "skills"))
    install_skills(agents, skills_dir)
    for agent in agents:
        console.print(f"[green]Installed skills into {agent.name}[/green] ({agent.skills_dir})")
```

- [ ] **Step 4.4: Wire into `src/lcagents/cli.py`**

```python
from lcagents.commands import info as info_cmd
from lcagents.commands import setup as setup_cmd

app.command("setup")(setup_cmd.setup)
```

- [ ] **Step 4.5: Run tests**

```bash
pytest -v
```
Expected: all green.

- [ ] **Step 4.6: Commit**

```bash
git add src/lcagents/skills src/lcagents/commands/setup.py src/lcagents/cli.py tests/test_setup.py
git commit -m "feat(setup): add lcagents setup command + skill plumbing"
```

---

## Task 5: Template engine

**Files:**
- Create: `src/lcagents/templating.py`
- Create: `tests/test_templating.py`
- Create: `tests/fixtures/templates/example/{{project_name}}/hello.py.j2`
- Create: `tests/fixtures/templates/example/static.txt`

- [ ] **Step 5.1: Author the test fixtures**

`tests/fixtures/templates/example/static.txt`:
```
this file is copied verbatim
```

`tests/fixtures/templates/example/{{project_name}}/hello.py.j2`:
```python
print("hello, {{ project_name }}")
```

- [ ] **Step 5.2: Write the failing test**

`tests/test_templating.py`:
```python
from pathlib import Path

import pytest

from lcagents.templating import render_template

FIXTURES = Path(__file__).parent / "fixtures" / "templates"


def test_render_copies_static_files(tmp_path: Path) -> None:
    render_template(
        source=FIXTURES / "example",
        dest=tmp_path,
        context={"project_name": "demo"},
    )
    assert (tmp_path / "static.txt").read_text() == "this file is copied verbatim\n"


def test_render_substitutes_in_paths_and_content(tmp_path: Path) -> None:
    render_template(
        source=FIXTURES / "example",
        dest=tmp_path,
        context={"project_name": "demo"},
    )
    rendered = tmp_path / "demo" / "hello.py"
    assert rendered.is_file()
    assert rendered.read_text() == 'print("hello, demo")\n'


def test_render_refuses_to_overwrite_existing_dest_files(tmp_path: Path) -> None:
    (tmp_path / "static.txt").write_text("DO NOT OVERWRITE")
    with pytest.raises(FileExistsError):
        render_template(
            source=FIXTURES / "example",
            dest=tmp_path,
            context={"project_name": "demo"},
        )
```

- [ ] **Step 5.3: Run to verify failure**

```bash
pytest tests/test_templating.py -v
```
Expected: ImportError.

- [ ] **Step 5.4: Implement `src/lcagents/templating.py`**

```python
"""Render a directory of Jinja2 templates into a destination directory.

Conventions:
- A path segment wrapped in `{{...}}` is rendered (so directory names can be templated).
- A file ending in `.j2` is rendered through Jinja2; the `.j2` is stripped.
- All other files are copied verbatim.
- Destination must not already contain any file we would write.
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from jinja2 import Environment, StrictUndefined


def render_template(source: Path, dest: Path, context: dict[str, Any]) -> None:
    env = Environment(undefined=StrictUndefined, keep_trailing_newline=True)

    planned: list[tuple[Path, Path, bool]] = []
    for src_path in sorted(source.rglob("*")):
        if src_path.is_dir():
            continue
        rel = src_path.relative_to(source)
        rendered_parts = [env.from_string(p).render(**context) for p in rel.parts]
        target_rel = Path(*rendered_parts)
        is_template = target_rel.suffix == ".j2"
        if is_template:
            target_rel = target_rel.with_suffix("")
        planned.append((src_path, dest / target_rel, is_template))

    for _, target, _ in planned:
        if target.exists():
            raise FileExistsError(target)

    for src_path, target, is_template in planned:
        target.parent.mkdir(parents=True, exist_ok=True)
        if is_template:
            rendered = env.from_string(src_path.read_text("utf-8")).render(**context)
            target.write_text(rendered, encoding="utf-8")
        else:
            shutil.copy2(src_path, target)
```

- [ ] **Step 5.5: Run tests**

```bash
pytest -v
```
Expected: all green.

- [ ] **Step 5.6: Commit**

```bash
git add src/lcagents/templating.py tests/test_templating.py tests/fixtures/
git commit -m "feat(templating): add Jinja2 template-tree renderer"
```

---

## Task 6: `_shared` template content

The files every template ships. Authored once, used by all three.

**Files:**
- Create: `src/lcagents/templates/_shared/.gitignore`
- Create: `src/lcagents/templates/_shared/.env.example.j2`
- Create: `src/lcagents/templates/_shared/README.md.j2`
- Create: `src/lcagents/templates/_shared/CLAUDE.md.j2`
- Create: `src/lcagents/templates/_shared/AGENTS.md.j2`
- Create: `src/lcagents/templates/_shared/.claude/settings.json`
- Create: `src/lcagents/templates/_shared/.agents/lcagents.toml.j2`
- Create: `src/lcagents/templates/_shared/langgraph.json`
- Create: `src/lcagents/templates/_shared/tests/test_agent.py`
- Create: `src/lcagents/templates/_shared/evals/datasets/smoke.jsonl`
- Create: `src/lcagents/templates/_shared/evals/evaluators.py`
- Create: `src/lcagents/templates/_shared/evals/run.py`

- [ ] **Step 6.1: Write each shared file**

`.gitignore`:
```
__pycache__/
.venv/
.env
.pytest_cache/
.ruff_cache/
.mypy_cache/
evals/results/
.agents/baseline/
```

`.env.example.j2`:
```
# Provider keys (uncomment what you use)
# OPENAI_API_KEY=
# ANTHROPIC_API_KEY=

# LangSmith - required for evals and `deploy langsmith`
LANGSMITH_API_KEY=
LANGSMITH_TRACING=true
LANGSMITH_PROJECT={{ project_name }}
```

`README.md.j2`:
```markdown
# {{ project_name }}

Scaffolded by `lcagents` (template: `{{ template }}`).

## Quickstart

    lcagents install
    cp .env.example .env  # then fill in keys
    lcagents run "hello"

## Commands

- `lcagents run "<prompt>"` — invoke the agent once
- `lcagents dev` — start the LangGraph dev server
- `lcagents eval run` — run LangSmith evals
- `lcagents deploy {{ deploy_target }}` — deploy

The agent is exported as `agent` from `agent/agent.py`. **Do not rename.**
```

`CLAUDE.md.j2`:
```markdown
# Project: {{ project_name }}

A LangChain agent project scaffolded by `lcagents` (template: `{{ template }}`).

## How to work in this repo

- Read `.agents/skills/project-overview.md` first.
- Template-specific guide: `.agents/skills/{{ template_skill }}.md`.
- Adding tools: `.agents/skills/adding-a-tool.md`.
- Evals: `.agents/skills/writing-evals.md`.
- Deploy: `.agents/skills/deploying.md`.

## Commands

- `lcagents run "<prompt>"` — smoke test the agent
- `lcagents dev` — interactive dev loop
- `lcagents eval run` — run LangSmith evals
- `lcagents deploy {{ deploy_target }}` — deploy

## Contract

The agent is always exported as `agent` from `agent/agent.py`. Do not rename.
```

`AGENTS.md.j2`: identical content to `CLAUDE.md.j2` (copy verbatim).

`.claude/settings.json`:
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "lcagents lint --quiet || true"
          }
        ]
      }
    ]
  }
}
```

`.agents/lcagents.toml.j2`:
```toml
template = "{{ template }}"
scaffolder_version = "{{ scaffolder_version }}"
deploy_target = "{{ deploy_target }}"
```

`langgraph.json` (not templated; same in every project):
```json
{
  "dependencies": ["."],
  "graphs": {
    "agent": "./agent/agent.py:agent"
  },
  "env": ".env",
  "python_version": "3.11"
}
```

`tests/test_agent.py`:
```python
from agent.agent import agent


def test_agent_is_invokable() -> None:
    assert hasattr(agent, "invoke")
```

`evals/datasets/smoke.jsonl`:
```
{"input": {"messages": [{"role": "user", "content": "Say hello in one word."}]}}
{"input": {"messages": [{"role": "user", "content": "What is 2 + 2?"}]}}
{"input": {"messages": [{"role": "user", "content": "Name a color."}]}}
```

`evals/evaluators.py`:
```python
"""LangSmith evaluators for this project. Edit freely."""
from __future__ import annotations

from typing import Any


def correctness(run: Any, example: Any) -> dict[str, Any]:
    """Trivial pass-through; replace with an LLM-as-judge for real use."""
    return {"key": "correctness", "score": 1.0, "comment": "stub"}


EVALUATORS = [correctness]
```

`evals/run.py`:
```python
"""Run LangSmith evals for this project.

Invoked by `lcagents eval run`, but also runnable directly: `python evals/run.py`.
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from agent.agent import agent
from evals.evaluators import EVALUATORS

ROOT = Path(__file__).resolve().parent
DATASETS = ROOT / "datasets"
RESULTS = ROOT / "results"


def _load_dataset(name: str) -> list[dict]:
    path = DATASETS / f"{name}.jsonl"
    return [json.loads(line) for line in path.read_text("utf-8").splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true", help="Run only the smoke dataset.")
    args = parser.parse_args()

    if not os.getenv("LANGSMITH_API_KEY"):
        print("ERROR: LANGSMITH_API_KEY is not set.")
        return 2

    datasets = ["smoke"] if args.smoke else [p.stem for p in DATASETS.glob("*.jsonl")]
    RESULTS.mkdir(exist_ok=True)
    results: dict[str, list[dict]] = {}

    try:
        from langsmith import evaluate as run_evaluation
    except ImportError:
        print("ERROR: langsmith not installed. Run `lcagents install`.")
        return 2

    for ds_name in datasets:
        examples = _load_dataset(ds_name)
        ds_results = run_evaluation(
            lambda inp: agent.invoke(inp),
            data=examples,
            evaluators=EVALUATORS,
            experiment_prefix=f"{ds_name}-",
        )
        results[ds_name] = list(ds_results)

    out = RESULTS / f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.write_text(json.dumps(results, default=str, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 6.2: Commit (no test yet — exercised end-to-end in Task 7)**

```bash
git add src/lcagents/templates/_shared/
git commit -m "feat(templates): add _shared template content (env, CLAUDE.md, AGENTS.md, evals scaffolding)"
```

---

## Task 7: `langgraph-agent` template + `scaffold` command

End-to-end slice: `lcagents scaffold create mything --template langgraph-agent` produces a runnable project tree on disk.

**Files:**
- Create: `src/lcagents/templates/langgraph-agent/agent/__init__.py`
- Create: `src/lcagents/templates/langgraph-agent/agent/agent.py.j2`
- Create: `src/lcagents/templates/langgraph-agent/agent/graph.py.j2`
- Create: `src/lcagents/templates/langgraph-agent/agent/tools.py.j2`
- Create: `src/lcagents/templates/langgraph-agent/agent/prompts.py.j2`
- Create: `src/lcagents/templates/langgraph-agent/pyproject.toml.j2`
- Create: `src/lcagents/project_skills/langgraph-agent/project-overview.md.j2`
- Create: `src/lcagents/project_skills/langgraph-agent/editing-the-graph.md`
- Create: `src/lcagents/project_skills/langgraph-agent/adding-a-tool.md`
- Create: `src/lcagents/project_skills/langgraph-agent/writing-evals.md`
- Create: `src/lcagents/project_skills/langgraph-agent/deploying.md.j2`
- Create: `src/lcagents/scaffold.py`
- Create: `src/lcagents/commands/scaffold.py`
- Modify: `src/lcagents/cli.py`
- Create: `tests/test_scaffold.py`

- [ ] **Step 7.1: Author template files**

`agent/__init__.py`: empty.

`agent/agent.py.j2`:
```python
"""Compiled LangGraph agent. Always exported as `agent`."""
from agent.graph import build_graph

agent = build_graph()
```

`agent/graph.py.j2`:
```python
"""StateGraph definition for {{ project_name }}."""
from __future__ import annotations

from langchain.chat_models import init_chat_model
from langgraph.graph import END, START, MessagesState, StateGraph

from agent.prompts import SYSTEM_PROMPT
from agent.tools import TOOLS

LLM = init_chat_model("openai:gpt-4o-mini").bind_tools(TOOLS)


def call_model(state: MessagesState) -> dict:
    response = LLM.invoke([{"role": "system", "content": SYSTEM_PROMPT}, *state["messages"]])
    return {"messages": [response]}


def build_graph():
    g = StateGraph(MessagesState)
    g.add_node("model", call_model)
    g.add_edge(START, "model")
    g.add_edge("model", END)
    return g.compile()
```

`agent/tools.py.j2`:
```python
"""User tools. Add new tools here and append them to TOOLS."""
from langchain_core.tools import tool


@tool
def echo(text: str) -> str:
    """Return the input unchanged."""
    return text


TOOLS = [echo]
```

`agent/prompts.py.j2`:
```python
SYSTEM_PROMPT = "You are {{ project_name }}, a helpful assistant."
```

`pyproject.toml.j2`:
```toml
[project]
name = "{{ project_name }}"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "langchain>=0.3",
    "langchain-openai>=0.2",
    "langgraph>=0.2",
    "langsmith>=0.1",
    "fastapi>=0.110",
    "uvicorn>=0.30",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "ruff>=0.5", "mypy>=1.10"]

[tool.setuptools.packages.find]
include = ["agent*", "evals*", "server*"]
```

- [ ] **Step 7.2: Author project-local skills**

`project-overview.md.j2`:
```markdown
---
name: project-overview
description: Use when starting work in this LangGraph agent project to learn the layout and the contract.
---

# {{ project_name }} — Project Overview

This is a **LangGraph agent project**.

## Layout

- `agent/agent.py` — exports the compiled graph as `agent`. **Never rename.**
- `agent/graph.py` — `StateGraph` definition; nodes, edges, compile.
- `agent/tools.py` — tool definitions; append to `TOOLS` list.
- `agent/prompts.py` — system prompt.
- `evals/` — LangSmith evalsets and runner.
- `server/` — FastAPI host for `lcagents deploy docker`.

## Common commands

- `lcagents run "<prompt>"` — invoke the agent once.
- `lcagents dev` — interactive dev server.
- `lcagents eval run` — run evals.
- `lcagents deploy {{ deploy_target }}` — deploy.
```

`editing-the-graph.md`:
```markdown
---
name: editing-the-graph
description: Use when adding nodes, edges, or conditional routing to the LangGraph agent.
---

# Editing the Graph

The graph lives in `agent/graph.py`. To add a node:

1. Define a function that takes `MessagesState` and returns `{"messages": [...]}`.
2. Call `g.add_node("name", fn)` inside `build_graph`.
3. Wire edges with `g.add_edge(...)` or `g.add_conditional_edges(...)`.

After editing, run `lcagents run "test prompt"` to confirm the graph still compiles.
```

`adding-a-tool.md`:
```markdown
---
name: adding-a-tool
description: Use when adding a new tool the agent can call.
---

# Adding a Tool

1. Open `agent/tools.py`.
2. Define the tool with `@tool` from `langchain_core.tools`.
3. Append it to the `TOOLS` list.
4. The graph picks it up automatically because `LLM.bind_tools(TOOLS)` is in `graph.py`.
5. Run `lcagents run "<prompt that should call the tool>"` to verify.
```

`writing-evals.md`:
```markdown
---
name: writing-evals
description: Use when adding eval examples or evaluators to this project.
---

# Writing Evals

- **Add an example:** append a JSON line to `evals/datasets/smoke.jsonl` (or create a new `.jsonl` file).
- **Add an evaluator:** define a function in `evals/evaluators.py` and append it to `EVALUATORS`.
- **Run:** `lcagents eval run`. Smoke-only: `lcagents eval run --smoke`.
- **Compare:** `lcagents eval compare evals/results/A.json evals/results/B.json`.

`LANGSMITH_API_KEY` must be set.
```

`deploying.md.j2`:
```markdown
---
name: deploying
description: Use when deploying this project. Default target is {{ deploy_target }}.
---

# Deploying

Default target: **{{ deploy_target }}**.

- `lcagents deploy langsmith` — push to LangSmith Cloud via `langgraph build/deploy`.
- `lcagents deploy docker --tag {{ project_name }}:latest` — build a self-contained image.

Both run `lcagents eval run --smoke` first and refuse to deploy if it fails.

**Never** print `.env` content into chat. Secrets live in `.env`; the deploy command pushes them to the right place.
```

- [ ] **Step 7.3: Implement `src/lcagents/scaffold.py`**

```python
"""Scaffold a new lcagents project on disk.

Composes _shared + a chosen template + project-local skills.
"""
from __future__ import annotations

from importlib.resources import files
from pathlib import Path

from lcagents import __version__
from lcagents.config import DeployTarget, Template
from lcagents.templating import render_template

# Maps template -> the project-local skill that's specific to that template
TEMPLATE_SKILL_MAP: dict[Template, str] = {
    "langgraph-agent": "editing-the-graph",
    "deep-agent": "adding-a-subagent",
    "langchain-chain": "editing-the-chain",
}


def scaffold_project(
    name: str,
    template: Template,
    deploy_target: DeployTarget,
    dest_parent: Path,
) -> Path:
    """Create a new project under `dest_parent / name`. Returns the project root."""
    project_root = dest_parent / name
    if project_root.exists():
        raise FileExistsError(project_root)

    context = {
        "project_name": name,
        "template": template,
        "deploy_target": deploy_target,
        "scaffolder_version": __version__,
        "template_skill": TEMPLATE_SKILL_MAP[template],
    }

    package_root = files("lcagents")
    shared = Path(str(package_root / "templates" / "_shared"))
    template_dir = Path(str(package_root / "templates" / template))
    skills_dir = Path(str(package_root / "project_skills" / template))

    project_root.mkdir(parents=True)
    render_template(shared, project_root, context)
    render_template(template_dir, project_root, context)
    render_template(skills_dir, project_root / ".agents" / "skills", context)

    return project_root
```

- [ ] **Step 7.4: Implement `src/lcagents/commands/scaffold.py`**

```python
"""`lcagents scaffold ...` command group."""
from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from lcagents.config import DeployTarget, Template
from lcagents.scaffold import scaffold_project

console = Console()
app = typer.Typer(help="Scaffold, enhance, or upgrade an lcagents project.")


@app.command("create", help="Create a new project.")
def create(
    name: str = typer.Argument(..., help="Project directory name to create."),
    template: Template = typer.Option(
        "langgraph-agent", "--template", "-t", help="Which template to use."
    ),
    deploy_target: DeployTarget = typer.Option(
        "docker", "--deploy-target", help="Default deploy target written into lcagents.toml."
    ),
) -> None:
    try:
        root = scaffold_project(name, template, deploy_target, Path.cwd())
    except FileExistsError as exc:
        console.print(f"[red]Refusing to overwrite existing path:[/red] {exc}")
        raise typer.Exit(1) from None

    console.print(f"[green]Scaffolded[/green] {root}")
    console.print(f"  Template: {template}")
    console.print(f"  Deploy target: {deploy_target}")
    console.print("\nNext steps:")
    console.print(f"  cd {name}")
    console.print("  lcagents install")
    console.print("  cp .env.example .env  # then fill in keys")
    console.print('  lcagents run "hello"')
```

- [ ] **Step 7.5: Wire into `src/lcagents/cli.py`**

```python
from lcagents.commands import scaffold as scaffold_cmd

app.add_typer(scaffold_cmd.app, name="scaffold")
```

- [ ] **Step 7.6: Write the test**

`tests/test_scaffold.py`:
```python
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
```

- [ ] **Step 7.7: Run tests**

```bash
pytest -v
```
Expected: all green.

- [ ] **Step 7.8: Commit**

```bash
git add src/lcagents/templates/langgraph-agent src/lcagents/project_skills/langgraph-agent \
        src/lcagents/scaffold.py src/lcagents/commands/scaffold.py src/lcagents/cli.py \
        tests/test_scaffold.py
git commit -m "feat(scaffold): add scaffold create + langgraph-agent template"
```

---

## Task 8: `run` command

**Files:**
- Create: `src/lcagents/commands/run.py`
- Modify: `src/lcagents/cli.py`
- Create: `tests/test_run.py`
- Create: `tests/fixtures/fake_project/agent/__init__.py`
- Create: `tests/fixtures/fake_project/agent/agent.py`
- Create: `tests/fixtures/fake_project/.agents/lcagents.toml`

- [ ] **Step 8.1: Author the test fixture project**

`tests/fixtures/fake_project/agent/__init__.py`: empty.

`tests/fixtures/fake_project/agent/agent.py`:
```python
class _FakeAgent:
    def invoke(self, payload):
        msg = payload["messages"][-1]["content"]
        return {"messages": [{"role": "assistant", "content": f"echo: {msg}"}]}


agent = _FakeAgent()
```

`tests/fixtures/fake_project/.agents/lcagents.toml`:
```toml
template = "langgraph-agent"
scaffolder_version = "0.1.0"
deploy_target = "docker"
```

- [ ] **Step 8.2: Write the failing test**

`tests/test_run.py`:
```python
import shutil
from pathlib import Path

from typer.testing import CliRunner

from lcagents.cli import app

runner = CliRunner()
FIXTURE = Path(__file__).parent / "fixtures" / "fake_project"


def test_run_invokes_agent_and_prints_response(tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "proj"
    shutil.copytree(FIXTURE, project)
    monkeypatch.chdir(project)

    result = runner.invoke(app, ["run", "hello world"])
    assert result.exit_code == 0
    assert "echo: hello world" in result.stdout


def test_run_fails_outside_project(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["run", "hi"])
    assert result.exit_code == 1
    assert "No lcagents project" in result.stdout
```

- [ ] **Step 8.3: Run to verify failure**

```bash
pytest tests/test_run.py -v
```
Expected: ImportError on `lcagents.commands.run`.

- [ ] **Step 8.4: Implement `src/lcagents/commands/run.py`**

```python
"""`lcagents run "<prompt>"` — invoke the project's `agent` once."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

import typer
from rich.console import Console

from lcagents.config import find_project_root

console = Console()


def run(prompt: str = typer.Argument(..., help="Prompt to send to the agent.")) -> None:
    """Invoke `agent.agent:agent` once with the given prompt."""
    project_root = find_project_root(Path.cwd())
    if project_root is None:
        console.print("[red]No lcagents project found in this directory.[/red]")
        raise typer.Exit(1)

    sys.path.insert(0, str(project_root))
    try:
        module = importlib.import_module("agent.agent")
    except ImportError as exc:
        console.print(f"[red]Could not import agent.agent:[/red] {exc}")
        raise typer.Exit(1) from None

    agent_obj = getattr(module, "agent", None)
    if agent_obj is None or not hasattr(agent_obj, "invoke"):
        console.print("[red]agent.agent must export `agent` with an .invoke() method.[/red]")
        raise typer.Exit(1)

    result = agent_obj.invoke({"messages": [{"role": "user", "content": prompt}]})
    _print_result(result)


def _print_result(result: object) -> None:
    if isinstance(result, dict) and "messages" in result:
        msgs = result["messages"]
        if msgs:
            last = msgs[-1]
            if isinstance(last, dict):
                console.print(last.get("content", ""))
            else:
                console.print(getattr(last, "content", str(last)))
            return
    console.print(str(result))
```

- [ ] **Step 8.5: Wire into CLI**

```python
from lcagents.commands import run as run_cmd

app.command("run")(run_cmd.run)
```

- [ ] **Step 8.6: Run tests**

```bash
pytest -v
```
Expected: all green.

- [ ] **Step 8.7: Commit**

```bash
git add src/lcagents/commands/run.py src/lcagents/cli.py tests/test_run.py tests/fixtures/fake_project
git commit -m "feat(run): add lcagents run for headless one-shot agent invocation"
```

---

## Task 9: `install`, `lint`, and `dev` commands

**Files:**
- Create: `src/lcagents/commands/install.py`
- Create: `src/lcagents/commands/lint.py`
- Create: `src/lcagents/commands/dev.py`
- Modify: `src/lcagents/cli.py`
- Create: `tests/test_wrappers.py`

- [ ] **Step 9.1: Write tests (mock subprocess)**

`tests/test_wrappers.py`:
```python
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
```

- [ ] **Step 9.2: Implement `src/lcagents/commands/install.py`**

```python
"""`lcagents install` — uv sync in the project root."""
from __future__ import annotations

import subprocess
from pathlib import Path

import typer
from rich.console import Console

from lcagents.config import find_project_root

console = Console()


def install() -> None:
    project = find_project_root(Path.cwd())
    if project is None:
        console.print("[red]No lcagents project found.[/red]")
        raise typer.Exit(1)
    proc = subprocess.run(["uv", "sync"], cwd=project)
    raise typer.Exit(proc.returncode)
```

- [ ] **Step 9.3: Implement `src/lcagents/commands/lint.py`**

```python
"""`lcagents lint` — ruff + mypy."""
from __future__ import annotations

import subprocess
from pathlib import Path

import typer
from rich.console import Console

from lcagents.config import find_project_root

console = Console()


def lint(quiet: bool = typer.Option(False, "--quiet", help="Suppress non-error output.")) -> None:
    project = find_project_root(Path.cwd())
    if project is None:
        console.print("[red]No lcagents project found.[/red]")
        raise typer.Exit(1)

    stdout = subprocess.DEVNULL if quiet else None
    ruff = subprocess.run(["ruff", "check", "."], cwd=project, stdout=stdout)
    mypy = subprocess.run(["mypy", "agent"], cwd=project, stdout=stdout)
    raise typer.Exit(max(ruff.returncode, mypy.returncode))
```

- [ ] **Step 9.4: Implement `src/lcagents/commands/dev.py`**

```python
"""`lcagents dev` — delegate to `langgraph dev`."""
from __future__ import annotations

import subprocess
from pathlib import Path

import typer
from rich.console import Console

from lcagents.config import find_project_root

console = Console()


def dev() -> None:
    project = find_project_root(Path.cwd())
    if project is None:
        console.print("[red]No lcagents project found.[/red]")
        raise typer.Exit(1)
    proc = subprocess.run(["langgraph", "dev"], cwd=project)
    raise typer.Exit(proc.returncode)
```

- [ ] **Step 9.5: Wire into CLI**

```python
from lcagents.commands import install as install_cmd
from lcagents.commands import lint as lint_cmd
from lcagents.commands import dev as dev_cmd

app.command("install")(install_cmd.install)
app.command("lint")(lint_cmd.lint)
app.command("dev")(dev_cmd.dev)
```

- [ ] **Step 9.6: Run tests**

```bash
pytest -v
```
Expected: all green.

- [ ] **Step 9.7: Commit**

```bash
git add src/lcagents/commands/install.py src/lcagents/commands/lint.py src/lcagents/commands/dev.py \
        src/lcagents/cli.py tests/test_wrappers.py
git commit -m "feat(cli): add install, lint, dev wrapper commands"
```

---

## Task 10: `deep-agent` template

Same shape as Task 7's langgraph-agent; only the `agent/` subtree and the template-specific skill differ.

**Files:**
- Create: `src/lcagents/templates/deep-agent/agent/__init__.py`
- Create: `src/lcagents/templates/deep-agent/agent/agent.py.j2`
- Create: `src/lcagents/templates/deep-agent/agent/subagents.py.j2`
- Create: `src/lcagents/templates/deep-agent/agent/tools.py.j2`
- Create: `src/lcagents/templates/deep-agent/agent/prompts.py.j2`
- Create: `src/lcagents/templates/deep-agent/pyproject.toml.j2`
- Create: 5 project-local skill files under `src/lcagents/project_skills/deep-agent/`
- Modify: `tests/test_scaffold.py`

- [ ] **Step 10.1: Author template files**

`agent/__init__.py`: empty.

`agent/agent.py.j2`:
```python
"""DeepAgent for {{ project_name }}. Always exported as `agent`."""
from deepagents import create_deep_agent
from langchain.chat_models import init_chat_model

from agent.prompts import SYSTEM_PROMPT
from agent.subagents import SUBAGENTS
from agent.tools import TOOLS

agent = create_deep_agent(
    model=init_chat_model("anthropic:claude-sonnet-4-5"),
    tools=TOOLS,
    subagents=SUBAGENTS,
    instructions=SYSTEM_PROMPT,
)
```

`agent/subagents.py.j2`:
```python
"""Sub-agents this DeepAgent can delegate to via the `task` tool."""
SUBAGENTS = [
    # {
    #     "name": "researcher",
    #     "description": "Searches the web and summarises findings.",
    #     "prompt": "You are a careful web researcher.",
    # },
]
```

`agent/tools.py.j2`:
```python
"""User tools available to the DeepAgent."""
from langchain_core.tools import tool


@tool
def echo(text: str) -> str:
    """Return the input unchanged."""
    return text


TOOLS = [echo]
```

`agent/prompts.py.j2`:
```python
SYSTEM_PROMPT = "You are {{ project_name }}, a helpful agent."
```

`pyproject.toml.j2`:
```toml
[project]
name = "{{ project_name }}"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "deepagents>=0.0.10",
    "langchain>=0.3",
    "langchain-anthropic>=0.2",
    "langgraph>=0.2",
    "langsmith>=0.1",
    "fastapi>=0.110",
    "uvicorn>=0.30",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "ruff>=0.5", "mypy>=1.10"]

[tool.setuptools.packages.find]
include = ["agent*", "evals*", "server*"]
```

- [ ] **Step 10.2: Author project-local skills**

`project-overview.md.j2`:
```markdown
---
name: project-overview
description: Use when starting work in this DeepAgents project to learn the layout.
---

# {{ project_name }} — Project Overview

This is a **DeepAgents project**.

## Layout

- `agent/agent.py` — exports `agent` from `create_deep_agent(...)`. **Never rename.**
- `agent/subagents.py` — sub-agent specifications for the `task` tool.
- `agent/tools.py` — tool definitions.
- `agent/prompts.py` — top-level system prompt / instructions.

DeepAgents already provides `write_todos`, virtual filesystem, and `task` delegation.

## Commands

- `lcagents run "<prompt>"`
- `lcagents dev` (works because DeepAgents returns a compiled LangGraph)
- `lcagents eval run`
- `lcagents deploy {{ deploy_target }}`
```

`adding-a-subagent.md`:
```markdown
---
name: adding-a-subagent
description: Use when adding a sub-agent the DeepAgent can delegate to.
---

# Adding a Sub-Agent

1. Open `agent/subagents.py`.
2. Append a dict to `SUBAGENTS` with keys: `name`, `description`, `prompt`. Optional: `tools`.
3. The DeepAgent will surface this sub-agent via its built-in `task` tool.

Example:

    SUBAGENTS = [
        {
            "name": "summariser",
            "description": "Compresses long text to bullet points.",
            "prompt": "You produce terse bullet summaries.",
        },
    ]
```

`adding-a-tool.md`: copy verbatim from `project_skills/langgraph-agent/adding-a-tool.md`.

`writing-evals.md`: copy verbatim from `project_skills/langgraph-agent/writing-evals.md`.

`deploying.md.j2`: copy verbatim from `project_skills/langgraph-agent/deploying.md.j2`.

- [ ] **Step 10.3: Extend `tests/test_scaffold.py`**

Append:
```python
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
```

- [ ] **Step 10.4: Run tests**

```bash
pytest -v
```
Expected: all green.

- [ ] **Step 10.5: Commit**

```bash
git add src/lcagents/templates/deep-agent src/lcagents/project_skills/deep-agent tests/test_scaffold.py
git commit -m "feat(scaffold): add deep-agent template + project skills"
```

---

## Task 11: `langchain-chain` template

**Files:**
- Create: `src/lcagents/templates/langchain-chain/agent/__init__.py`
- Create: `src/lcagents/templates/langchain-chain/agent/agent.py.j2`
- Create: `src/lcagents/templates/langchain-chain/agent/chain.py.j2`
- Create: `src/lcagents/templates/langchain-chain/agent/tools.py.j2`
- Create: `src/lcagents/templates/langchain-chain/agent/prompts.py.j2`
- Create: `src/lcagents/templates/langchain-chain/pyproject.toml.j2`
- Create: 5 project-local skill files under `src/lcagents/project_skills/langchain-chain/`
- Modify: `tests/test_scaffold.py`

- [ ] **Step 11.1: Author template files**

`agent/__init__.py`: empty.

`agent/agent.py.j2`:
```python
"""LCEL chain for {{ project_name }}. Exposed as `agent` (a Runnable)."""
from agent.chain import build_chain

agent = build_chain()
```

`agent/chain.py.j2`:
```python
"""LCEL chain definition."""
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import Runnable, RunnableLambda

from agent.prompts import SYSTEM_PROMPT


def build_chain() -> Runnable:
    llm = init_chat_model("openai:gpt-4o-mini")

    def to_messages(payload: dict) -> list:
        msgs = [SystemMessage(content=SYSTEM_PROMPT)]
        for m in payload.get("messages", []):
            msgs.append(HumanMessage(content=m["content"]))
        return msgs

    return RunnableLambda(to_messages) | llm
```

`agent/tools.py.j2`:
```python
"""For LCEL chains, 'tools' usually means callables you compose into the chain.

Add helpers here and wire them into agent/chain.py.
"""
```

`agent/prompts.py.j2`:
```python
SYSTEM_PROMPT = "You are {{ project_name }}."
```

`pyproject.toml.j2`:
```toml
[project]
name = "{{ project_name }}"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "langchain>=0.3",
    "langchain-openai>=0.2",
    "langgraph>=0.2",
    "langsmith>=0.1",
    "fastapi>=0.110",
    "uvicorn>=0.30",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "ruff>=0.5", "mypy>=1.10"]

[tool.setuptools.packages.find]
include = ["agent*", "evals*", "server*"]
```

- [ ] **Step 11.2: Author project-local skills**

`project-overview.md.j2`:
```markdown
---
name: project-overview
description: Use when starting work in this LangChain LCEL chain project.
---

# {{ project_name }} — Project Overview

This is a **LangChain Expression Language (LCEL) project** — a `Runnable` pipeline, not an agentic graph.

## Layout

- `agent/agent.py` — exports the chain as `agent`. **Never rename.**
- `agent/chain.py` — LCEL composition (the `build_chain()` function).
- `agent/tools.py` — callables you compose into the chain.
- `agent/prompts.py` — system prompt.

## Commands

- `lcagents run "<prompt>"`
- `lcagents eval run`
- `lcagents deploy {{ deploy_target }}`

`lcagents dev` is a no-op for chain projects (no graph to inspect).
```

`editing-the-chain.md`:
```markdown
---
name: editing-the-chain
description: Use when modifying the LCEL chain composition in agent/chain.py.
---

# Editing the Chain

LCEL composes `Runnable`s with the `|` operator. Common building blocks:

- `RunnableLambda(fn)` — wraps a Python function.
- `RunnableParallel({"a": ra, "b": rb})` — fan-out.
- `RunnablePassthrough.assign(...)` — annotate the payload.
- `chat_model | parser` — terminate with a parser.

Compose left-to-right; the result of one stage is the input to the next.
```

`adding-a-tool.md`:
```markdown
---
name: adding-a-tool
description: Use when adding a callable to compose into the LCEL chain.
---

# Adding a Tool (LCEL chains)

For LCEL chains, "tool" usually means: a function you wrap with `RunnableLambda` and pipe into the chain.

1. Open `agent/tools.py` and add the function.
2. Open `agent/chain.py` and import + compose it.
3. `lcagents run "<prompt>"` to verify.
```

`writing-evals.md`: copy verbatim from `project_skills/langgraph-agent/writing-evals.md`.

`deploying.md.j2`: copy verbatim from `project_skills/langgraph-agent/deploying.md.j2`.

- [ ] **Step 11.3: Extend `tests/test_scaffold.py`**

```python
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
```

- [ ] **Step 11.4: Run tests**

```bash
pytest -v
```
Expected: all green.

- [ ] **Step 11.5: Commit**

```bash
git add src/lcagents/templates/langchain-chain src/lcagents/project_skills/langchain-chain tests/test_scaffold.py
git commit -m "feat(scaffold): add langchain-chain template + project skills"
```

---

## Task 12: `eval run` and `eval compare` commands

`eval run` shells out to the project's `evals/run.py`. `eval compare` reads two JSON result files and prints a delta table. Note: the Python module is named `evals.py` (plural) to avoid shadowing the built-in `eval` keyword; the user-facing CLI subcommand is `eval`.

**Files:**
- Create: `src/lcagents/commands/evals.py`
- Modify: `src/lcagents/cli.py`
- Create: `tests/test_evals.py`
- Create: `tests/fixtures/eval_results/a.json`
- Create: `tests/fixtures/eval_results/b.json`

- [ ] **Step 12.1: Author the result fixtures**

`tests/fixtures/eval_results/a.json`:
```json
{
  "smoke": [
    {"key": "correctness", "score": 0.8},
    {"key": "latency", "score": 1.2}
  ]
}
```

`tests/fixtures/eval_results/b.json`:
```json
{
  "smoke": [
    {"key": "correctness", "score": 0.9},
    {"key": "latency", "score": 1.5}
  ]
}
```

- [ ] **Step 12.2: Write the failing test**

`tests/test_evals.py`:
```python
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
```

- [ ] **Step 12.3: Implement `src/lcagents/commands/evals.py`**

```python
"""`lcagents eval run` and `lcagents eval compare`.

Module name is plural (`evals`) to avoid shadowing Python's built-in `eval`.
The user-facing CLI subcommand is singular: `lcagents eval ...`.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from lcagents.config import find_project_root

console = Console()
app = typer.Typer(help="Run and compare LangSmith evals.")


@app.command("run")
def run_cmd(smoke: bool = typer.Option(False, "--smoke", help="Run only smoke dataset.")) -> None:
    """Run the project's evals/run.py."""
    project = find_project_root(Path.cwd())
    if project is None:
        console.print("[red]No lcagents project found.[/red]")
        raise typer.Exit(1)
    if not os.getenv("LANGSMITH_API_KEY"):
        console.print("[red]LANGSMITH_API_KEY is not set. Run `lcagents login`.[/red]")
        raise typer.Exit(2)

    cmd = [sys.executable, str(project / "evals" / "run.py")]
    if smoke:
        cmd.append("--smoke")
    proc = subprocess.run(cmd, cwd=project)
    raise typer.Exit(proc.returncode)


@app.command("compare")
def compare_cmd(a: Path, b: Path) -> None:
    """Diff two eval result JSON files."""
    da = json.loads(a.read_text("utf-8"))
    db = json.loads(b.read_text("utf-8"))

    table = Table(title=f"{a.name}  ->  {b.name}")
    table.add_column("dataset")
    table.add_column("metric")
    table.add_column(a.name)
    table.add_column(b.name)
    table.add_column("delta")

    for ds in sorted(set(da) | set(db)):
        scores_a = {r["key"]: r["score"] for r in da.get(ds, [])}
        scores_b = {r["key"]: r["score"] for r in db.get(ds, [])}
        for key in sorted(set(scores_a) | set(scores_b)):
            sa = scores_a.get(key)
            sb = scores_b.get(key)
            delta = (sb - sa) if (sa is not None and sb is not None) else None
            delta_str = f"{delta:+.2f}" if delta is not None else "-"
            table.add_row(ds, key, _fmt(sa), _fmt(sb), delta_str)

    console.print(table)


def _fmt(v: float | None) -> str:
    return "-" if v is None else f"{v:.2f}"
```

- [ ] **Step 12.4: Wire into CLI**

```python
from lcagents.commands import evals as evals_cmd

app.add_typer(evals_cmd.app, name="eval")
```

- [ ] **Step 12.5: Run tests**

```bash
pytest -v
```
Expected: all green.

- [ ] **Step 12.6: Commit**

```bash
git add src/lcagents/commands/evals.py src/lcagents/cli.py tests/test_evals.py tests/fixtures/eval_results
git commit -m "feat(evals): add eval run and eval compare commands"
```

---

## Task 13: `server/` template + `deploy docker` command

**Files:**
- Create: `src/lcagents/templates/_shared/server/__init__.py`
- Create: `src/lcagents/templates/_shared/server/app.py.j2`
- Create: `src/lcagents/templates/_shared/server/Dockerfile`
- Create: `src/lcagents/commands/deploy.py`
- Modify: `src/lcagents/cli.py`
- Modify: `tests/test_scaffold.py` (add server files to expected list)
- Create: `tests/test_deploy_docker.py`

- [ ] **Step 13.1: Author the server template files**

`server/__init__.py`: empty.

`server/app.py.j2`:
```python
"""Tiny FastAPI host for {{ project_name }}.

POST /invoke   {"input": {"messages": [...]}}
POST /stream   (NDJSON)
"""
from __future__ import annotations

import json
from collections.abc import AsyncGenerator

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

load_dotenv()

from agent.agent import agent  # noqa: E402

app = FastAPI(title="{{ project_name }}")


class InvokeRequest(BaseModel):
    input: dict


@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True}


@app.post("/invoke")
def invoke(req: InvokeRequest) -> dict:
    return {"output": agent.invoke(req.input)}


@app.post("/stream")
async def stream(req: InvokeRequest) -> StreamingResponse:
    async def gen() -> AsyncGenerator[bytes, None]:
        async for chunk in agent.astream(req.input):
            yield (json.dumps(chunk, default=str) + "\n").encode("utf-8")

    return StreamingResponse(gen(), media_type="application/x-ndjson")
```

`server/Dockerfile`:
```dockerfile
# syntax=docker/dockerfile:1.7

FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS build
WORKDIR /app
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev || uv sync --no-dev
COPY agent/ ./agent/
COPY server/ ./server/

FROM python:3.11-slim AS runtime
RUN useradd -m -u 1000 app
WORKDIR /app
COPY --from=build /app /app
ENV PATH="/app/.venv/bin:$PATH"
USER app
EXPOSE 8080
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8080"]
```

- [ ] **Step 13.2: Write the failing test (Docker SDK mocked)**

`tests/test_deploy_docker.py`:
```python
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
```

- [ ] **Step 13.3: Implement `src/lcagents/commands/deploy.py`**

```python
"""`lcagents deploy {langsmith,docker}`."""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import docker  # type: ignore[import-untyped]
import httpx
import typer
from rich.console import Console

from lcagents.config import find_project_root

console = Console()
app = typer.Typer(help="Deploy the agent.")


def _smoke_check(project: Path) -> int:
    """Run the smoke dataset as a deploy gate."""
    if not os.getenv("LANGSMITH_API_KEY"):
        console.print("[red]LANGSMITH_API_KEY required for the smoke pre-flight.[/red]")
        return 2
    proc = subprocess.run(
        [sys.executable, str(project / "evals" / "run.py"), "--smoke"],
        cwd=project,
    )
    return proc.returncode


@app.command("docker")
def docker_deploy(
    tag: str = typer.Option(..., "--tag", help="Image tag, e.g. my-agent:latest"),
    push: str | None = typer.Option(None, "--push", help="Optional registry to push to"),
) -> None:
    project = find_project_root(Path.cwd())
    if project is None:
        console.print("[red]No lcagents project found.[/red]")
        raise typer.Exit(1)

    console.print("[bold]Pre-flight: smoke check[/bold]")
    rc = _smoke_check(project)
    if rc != 0:
        console.print("[red]Smoke check failed; refusing to build.[/red]")
        raise typer.Exit(1)

    client = docker.from_env()
    console.print(f"[bold]Building image[/bold] {tag}")
    image, _logs = client.images.build(
        path=str(project), dockerfile="server/Dockerfile", tag=tag, rm=True
    )
    console.print(f"[green]Built[/green] {image.id}")

    if push:
        full = f"{push}/{tag}"
        client.images.get(tag).tag(full)
        client.images.push(full)
        console.print(f"[green]Pushed[/green] {full}")

    console.print("[bold]Smoke-testing the container[/bold]")
    container = client.containers.run(tag, detach=True, ports={"8080/tcp": None}, environment={})
    try:
        container.reload()
        port = container.attrs["NetworkSettings"]["Ports"]["8080/tcp"][0]["HostPort"]
        time.sleep(2)
        resp = httpx.post(
            f"http://localhost:{port}/invoke",
            json={"input": {"messages": [{"role": "user", "content": "hello"}]}},
            timeout=30,
        )
        if resp.status_code != 200:
            console.print(f"[red]Container responded with {resp.status_code}[/red]")
            raise typer.Exit(1)
        console.print(f"[green]Container OK[/green] (port {port})")
    finally:
        container.stop()
        container.remove()

    console.print(f"\nRun it: [bold]docker run --env-file .env -p 8080:8080 {tag}[/bold]")


@app.command("langsmith")
def langsmith_deploy() -> None:
    project = find_project_root(Path.cwd())
    if project is None:
        console.print("[red]No lcagents project found.[/red]")
        raise typer.Exit(1)

    console.print("[bold]Pre-flight: smoke check[/bold]")
    if _smoke_check(project) != 0:
        console.print("[red]Smoke check failed; refusing to deploy.[/red]")
        raise typer.Exit(1)

    console.print("[bold]Building with langgraph[/bold]")
    rc = subprocess.run(["langgraph", "build", "-t", project.name], cwd=project).returncode
    if rc != 0:
        raise typer.Exit(rc)

    rc = subprocess.run(["langgraph", "deploy"], cwd=project).returncode
    raise typer.Exit(rc)
```

- [ ] **Step 13.4: Wire into CLI**

```python
from lcagents.commands import deploy as deploy_cmd

app.add_typer(deploy_cmd.app, name="deploy")
```

- [ ] **Step 13.5: Update `tests/test_scaffold.py` `EXPECTED_FILES`**

Add `"server/__init__.py"`, `"server/app.py"`, `"server/Dockerfile"` to the list.

- [ ] **Step 13.6: Run all tests**

```bash
pytest -v
```
Expected: all green.

- [ ] **Step 13.7: Commit**

```bash
git add src/lcagents/templates/_shared/server src/lcagents/commands/deploy.py \
        src/lcagents/cli.py tests/test_scaffold.py tests/test_deploy_docker.py
git commit -m "feat(deploy): add docker + langsmith deploy paths with smoke pre-flight"
```

---

## Task 14: `login` command

**Files:**
- Create: `src/lcagents/commands/login.py`
- Modify: `src/lcagents/cli.py`
- Create: `tests/test_login.py`

- [ ] **Step 14.1: Write the failing test**

`tests/test_login.py`:
```python
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
```

- [ ] **Step 14.2: Implement `src/lcagents/commands/login.py`**

```python
"""`lcagents login` — populate .env from .env.example interactively."""
from __future__ import annotations

from pathlib import Path

import questionary
import typer
from rich.console import Console

from lcagents.config import find_project_root

console = Console()


def login(status: bool = typer.Option(False, "--status", help="Show which keys are set.")) -> None:
    project = find_project_root(Path.cwd())
    if project is None:
        console.print("[red]No lcagents project found.[/red]")
        raise typer.Exit(1)

    env_path = project / ".env"
    example_path = project / ".env.example"

    if status:
        existing = _parse_env(env_path) if env_path.exists() else {}
        for key in _keys_from_example(example_path):
            mark = "set" if existing.get(key) else "[yellow]missing[/yellow]"
            console.print(f"  {key}: {mark}")
        return

    keys = _keys_from_example(example_path)
    existing = _parse_env(env_path) if env_path.exists() else {}
    for key in keys:
        if existing.get(key):
            continue
        value = questionary.password(f"{key}:").ask()
        if value:
            existing[key] = value

    env_path.write_text("\n".join(f"{k}={v}" for k, v in existing.items()) + "\n")
    console.print(f"[green]Wrote[/green] {env_path}")


def _keys_from_example(path: Path) -> list[str]:
    keys: list[str] = []
    if not path.exists():
        return keys
    for raw in path.read_text("utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        keys.append(line.split("=", 1)[0])
    return keys


def _parse_env(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in path.read_text("utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k] = v
    return out
```

- [ ] **Step 14.3: Wire into CLI**

```python
from lcagents.commands import login as login_cmd

app.command("login")(login_cmd.login)
```

- [ ] **Step 14.4: Run tests**

```bash
pytest -v
```
Expected: all green.

- [ ] **Step 14.5: Commit**

```bash
git add src/lcagents/commands/login.py src/lcagents/cli.py tests/test_login.py
git commit -m "feat(login): add interactive .env editor and --status flag"
```

---

## Task 15: `scaffold enhance` command

**Files:**
- Modify: `src/lcagents/scaffold.py`
- Modify: `src/lcagents/commands/scaffold.py`
- Create: `tests/test_enhance.py`

- [ ] **Step 15.1: Write the failing test**

`tests/test_enhance.py`:
```python
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
```

- [ ] **Step 15.2: Append enhance helpers to `src/lcagents/scaffold.py`**

```python
import shutil
import tempfile
from dataclasses import replace
from typing import Iterable

from lcagents.config import load_config, save_config

ENHANCEMENT_PATHS: dict[str, list[str]] = {
    "docker": ["server"],
    "evals": ["evals"],
}


def enhance_project(
    project_root: Path,
    add: Iterable[str],
    target: DeployTarget | None,
) -> tuple[list[str], list[str]]:
    """Apply enhancements. Returns (added_subtrees, already_present_subtrees)."""
    cfg = load_config(project_root)
    context = {
        "project_name": project_root.name,
        "template": cfg.template,
        "deploy_target": cfg.deploy_target,
        "scaffolder_version": __version__,
        "template_skill": TEMPLATE_SKILL_MAP[cfg.template],
    }
    package_root = files("lcagents")
    shared = Path(str(package_root / "templates" / "_shared"))

    added: list[str] = []
    already: list[str] = []
    for sub in add:
        targets = ENHANCEMENT_PATHS.get(sub)
        if not targets:
            raise ValueError(f"Unknown enhancement: {sub}")
        if all((project_root / t).exists() for t in targets):
            already.append(sub)
            continue
        with tempfile.TemporaryDirectory() as td:
            staging = Path(td) / "stage"
            staging.mkdir()
            render_template(shared, staging, context)
            for t in targets:
                src = staging / t
                if not src.exists():
                    continue
                shutil.copytree(src, project_root / t, dirs_exist_ok=True)
        added.append(sub)

    if target is not None:
        save_config(project_root, replace(cfg, deploy_target=target))

    return added, already
```

- [ ] **Step 15.3: Wire `enhance` subcommand in `src/lcagents/commands/scaffold.py`**

Add at the top:
```python
from typing import List

from lcagents.config import find_project_root
from lcagents.scaffold import enhance_project
```

Add the command:
```python
@app.command("enhance", help="Add deploy/evals or switch deploy target.")
def enhance(
    add: List[str] = typer.Option([], "--add", help="Subsystem(s) to add: docker, evals."),
    target: DeployTarget | None = typer.Option(None, "--target", help="Switch default deploy target."),
) -> None:
    project = find_project_root(Path.cwd())
    if project is None:
        console.print("[red]No lcagents project found.[/red]")
        raise typer.Exit(1)

    added, already = enhance_project(project, add, target)
    for a in added:
        console.print(f"[green]Added[/green] {a}")
    for a in already:
        console.print(f"[yellow]{a} already present[/yellow]")
    if target:
        console.print(f"[green]Set deploy_target = {target}[/green]")
```

- [ ] **Step 15.4: Run tests**

```bash
pytest -v
```
Expected: all green.

- [ ] **Step 15.5: Commit**

```bash
git add src/lcagents/scaffold.py src/lcagents/commands/scaffold.py tests/test_enhance.py
git commit -m "feat(scaffold): add enhance for docker/evals/target switch"
```

---

## Task 16: `scaffold upgrade` command (3-way merge)

**Files:**
- Create: `src/lcagents/upgrade.py`
- Modify: `src/lcagents/commands/scaffold.py`
- Create: `tests/test_upgrade.py`

- [ ] **Step 16.1: Write the failing test**

`tests/test_upgrade.py`:
```python
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
```

- [ ] **Step 16.2: Implement `src/lcagents/upgrade.py`**

```python
"""3-way merge for `lcagents scaffold upgrade`.

Strategy:
- Snapshot of originally-rendered files lives at `.agents/baseline/`.
  Created lazily on first upgrade if missing — older projects then assume
  "user content == baseline", which means non-edited files upgrade cleanly.
- For each tracked file:
    base    = baseline content
    current = file in project today
    new     = freshly-rendered template content
  - base == current      → overwrite with `new`
  - current == new       → no change
  - all three differ     → write `<file>.lcagents-upgrade.txt` with `new` + diff header;
                           leave current untouched
- After upgrade, refresh baseline snapshot.
"""
from __future__ import annotations

import shutil
import tempfile
from dataclasses import replace
from importlib.resources import files
from pathlib import Path
from typing import Iterable

from lcagents import __version__
from lcagents.config import load_config, save_config
from lcagents.scaffold import TEMPLATE_SKILL_MAP
from lcagents.templating import render_template

TRACKED: tuple[str, ...] = (
    "CLAUDE.md",
    "AGENTS.md",
    ".agents/skills",
    "server/Dockerfile",
)

BASELINE_DIR = Path(".agents") / "baseline"


def _walk(root: Path, rels: Iterable[str]) -> list[Path]:
    out: list[Path] = []
    for rel in rels:
        path = root / rel
        if not path.exists():
            continue
        if path.is_file():
            out.append(path)
        else:
            out.extend(p for p in path.rglob("*") if p.is_file())
    return out


def upgrade_project(project_root: Path) -> tuple[list[Path], list[Path]]:
    cfg = load_config(project_root)
    context = {
        "project_name": project_root.name,
        "template": cfg.template,
        "deploy_target": cfg.deploy_target,
        "scaffolder_version": __version__,
        "template_skill": TEMPLATE_SKILL_MAP[cfg.template],
    }

    package_root = files("lcagents")
    shared = Path(str(package_root / "templates" / "_shared"))
    template_dir = Path(str(package_root / "templates" / cfg.template))
    skills_dir = Path(str(package_root / "project_skills" / cfg.template))

    with tempfile.TemporaryDirectory() as td:
        fresh = Path(td) / "fresh"
        fresh.mkdir()
        render_template(shared, fresh, context)
        render_template(template_dir, fresh, context)
        render_template(skills_dir, fresh / ".agents" / "skills", context)

        baseline_root = project_root / BASELINE_DIR
        updated: list[Path] = []
        conflicts: list[Path] = []

        for fresh_file in _walk(fresh, TRACKED):
            rel = fresh_file.relative_to(fresh)
            current = project_root / rel
            base = baseline_root / rel

            new_text = fresh_file.read_text("utf-8")
            cur_text = current.read_text("utf-8") if current.exists() else None
            base_text = base.read_text("utf-8") if base.exists() else cur_text

            if cur_text is None:
                current.parent.mkdir(parents=True, exist_ok=True)
                current.write_text(new_text, "utf-8")
                updated.append(current)
                continue

            if cur_text == base_text:
                if cur_text != new_text:
                    current.write_text(new_text, "utf-8")
                    updated.append(current)
                continue

            if new_text == cur_text:
                continue

            conflict_path = current.with_suffix(current.suffix + ".lcagents-upgrade.txt")
            header = (
                "# Conflict from `lcagents scaffold upgrade`\n"
                f"# Your file at {rel} was modified.\n"
                "# Below is the new template content. Merge manually and delete this file.\n\n"
            )
            conflict_path.write_text(header + new_text, "utf-8")
            conflicts.append(conflict_path)

        if baseline_root.exists():
            shutil.rmtree(baseline_root)
        for fresh_file in _walk(fresh, TRACKED):
            rel = fresh_file.relative_to(fresh)
            target = baseline_root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(fresh_file, target)

    save_config(project_root, replace(cfg, scaffolder_version=__version__))
    return updated, conflicts
```

- [ ] **Step 16.3: Wire `upgrade` in `src/lcagents/commands/scaffold.py`**

```python
from lcagents.upgrade import upgrade_project


@app.command("upgrade", help="Re-sync skill files and template content.")
def upgrade() -> None:
    project = find_project_root(Path.cwd())
    if project is None:
        console.print("[red]No lcagents project found.[/red]")
        raise typer.Exit(1)
    updated, conflicts = upgrade_project(project)
    for u in updated:
        console.print(f"[green]Updated[/green] {u.relative_to(project)}")
    for c in conflicts:
        console.print(f"[yellow]Conflict[/yellow] {c.relative_to(project)}")
```

- [ ] **Step 16.4: Run tests**

```bash
pytest -v
```
Expected: all green.

- [ ] **Step 16.5: Commit**

```bash
git add src/lcagents/upgrade.py src/lcagents/commands/scaffold.py tests/test_upgrade.py
git commit -m "feat(scaffold): add upgrade with 3-way merge and baseline tracking"
```

---

## Task 17: Author the eight global skill files

These ship to coding agents via `setup`. Documentation, not code, but they're the product's surface — write them carefully.

**Files (all under `src/lcagents/skills/`):**
- Modify: `lcagents-workflow.md` (replace stub from Task 4)
- Create: `lcagents-scaffold.md`
- Create: `lcagents-langgraph-code.md`
- Create: `lcagents-deepagents-code.md`
- Create: `lcagents-langchain-code.md`
- Create: `lcagents-langsmith-evals.md`
- Create: `lcagents-deploy.md`
- Create: `lcagents-observability.md`

Each file MUST start with YAML frontmatter (name + description). The description must be specific enough that a coding agent can decide whether to load the skill.

- [ ] **Step 17.1: Author `lcagents-workflow.md`**

```markdown
---
name: lcagents-workflow
description: Use when scaffolding a LangChain agent project, or when working in any project with .agents/lcagents.toml. Teaches the develop -> evals -> deploy lifecycle and which command to reach for at each step.
---

# lcagents Workflow

`lcagents` is a Python CLI for scaffolding, running, evaluating, and deploying LangChain / LangGraph / DeepAgents projects. **It is a tool for you (the coding agent), not a coding agent itself.** Don't try to use it to chat or reason; use it to take actions.

## When to invoke which command

| Goal | Command |
|---|---|
| Start a new project | `lcagents scaffold create <name> --template {langgraph-agent\|deep-agent\|langchain-chain}` |
| Install deps | `lcagents install` |
| Set provider/LangSmith keys | `lcagents login` |
| Smoke-test the agent | `lcagents run "<prompt>"` |
| Interactive dev | `lcagents dev` |
| Run evals | `lcagents eval run` (or `--smoke` for the 3-row dataset) |
| Compare evals | `lcagents eval compare a.json b.json` |
| Deploy | `lcagents deploy {langsmith\|docker}` |
| Add docker/evals to existing project | `lcagents scaffold enhance --add {docker\|evals}` |
| Re-sync after a CLI bump | `lcagents scaffold upgrade` |

## Hard rules

- The runnable agent is **always** exported as `agent` from `agent/agent.py`. Never rename it.
- Read the project-local skills under `.agents/skills/` before editing — they describe the specific shape of *this* project.
- Both `deploy` commands run a smoke pre-flight. If they refuse, fix the agent or the smoke dataset; do not bypass.
- `LANGSMITH_API_KEY` is required for evals and the LangSmith deploy path.
```

- [ ] **Step 17.2: Author `lcagents-scaffold.md`**

```markdown
---
name: lcagents-scaffold
description: Use when creating a new lcagents project, when adding deploy/evals to an existing one, or when upgrading a project to a newer CLI version.
---

# lcagents Scaffolding

## Templates

- **`langgraph-agent`** — full StateGraph control. Pick when the user wants explicit nodes/edges/conditional routing.
- **`deep-agent`** — uses `create_deep_agent`. Pick for batteries-included planning agents with sub-agents and a virtual filesystem.
- **`langchain-chain`** — LCEL `Runnable` pipeline. Pick for non-agentic flows: RAG, summarisation, classification.

## Create

    lcagents scaffold create my-project --template langgraph-agent --deploy-target docker

The CLI refuses to overwrite an existing directory.

## Enhance an existing project

- `lcagents scaffold enhance --add docker` — drops in `server/` + Dockerfile if missing.
- `lcagents scaffold enhance --add evals` — drops in `evals/` scaffolding.
- `lcagents scaffold enhance --target {langsmith|docker}` — switches the default deploy target in `.agents/lcagents.toml`.

## Upgrade

`lcagents scaffold upgrade` re-syncs `CLAUDE.md`, `AGENTS.md`, `.agents/skills/`, and `server/Dockerfile` to the current CLI's template content using a 3-way merge against `.agents/baseline/`. Conflicts are written as `<file>.lcagents-upgrade.txt` next to the original; resolve them by hand and delete the conflict file.
```

- [ ] **Step 17.3: Author `lcagents-langgraph-code.md`**

```markdown
---
name: lcagents-langgraph-code
description: Use when editing a LangGraph project — adding nodes, edges, conditional routing, checkpointers, streaming, or state schemas.
---

# LangGraph Code Patterns

## Graph construction

    from langgraph.graph import StateGraph, START, END, MessagesState

    g = StateGraph(MessagesState)
    g.add_node("model", call_model)
    g.add_edge(START, "model")
    g.add_edge("model", END)
    agent = g.compile()

## Conditional routing

    def route(state) -> str:
        return "tools" if state["messages"][-1].tool_calls else END

    g.add_conditional_edges("model", route, {"tools": "tools", END: END})

## Tool nodes

    from langgraph.prebuilt import ToolNode
    g.add_node("tools", ToolNode(TOOLS))

## Checkpointers (persistence)

    from langgraph.checkpoint.memory import MemorySaver
    agent = g.compile(checkpointer=MemorySaver())

## Streaming

    for chunk in agent.stream({"messages": [...]}, stream_mode="updates"):
        ...
```

- [ ] **Step 17.4: Author `lcagents-deepagents-code.md`**

```markdown
---
name: lcagents-deepagents-code
description: Use when editing a DeepAgents project — adding tools, sub-agents, modifying the system prompt, or working with the virtual filesystem.
---

# DeepAgents Code Patterns

## Construction

    from deepagents import create_deep_agent
    agent = create_deep_agent(model=..., tools=TOOLS, subagents=SUBAGENTS, instructions=PROMPT)

`create_deep_agent` returns a compiled LangGraph — `.invoke`, `.stream`, `.astream` all work.

## Sub-agents

    SUBAGENTS = [
        {"name": "researcher", "description": "...", "prompt": "..."},
    ]

The DeepAgent automatically exposes a `task` tool that delegates to the sub-agent by name.

## Built-ins

DeepAgents already provides: `write_todos` (planning), `read_file` / `write_file` / `edit_file` / `ls` / `glob` / `grep` (virtual FS), `task` (sub-agent delegation), context auto-summarisation. Don't re-implement them.
```

- [ ] **Step 17.5: Author `lcagents-langchain-code.md`**

```markdown
---
name: lcagents-langchain-code
description: Use when editing a LangChain LCEL chain project — composing Runnables, retrievers, embeddings, chat models, parsers.
---

# LangChain (LCEL) Code Patterns

LCEL composes `Runnable`s with `|`.

## Building blocks

- `RunnableLambda(fn)` — wrap a Python callable.
- `RunnableParallel({"a": ra, "b": rb})` — fan-out.
- `RunnablePassthrough.assign(...)` — annotate the payload.
- `chat_model | parser` — terminate.

## Retrieval pattern

    retriever = vectorstore.as_retriever()
    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt | llm | parser
    )
```

- [ ] **Step 17.6: Author `lcagents-langsmith-evals.md`**

```markdown
---
name: lcagents-langsmith-evals
description: Use when authoring eval datasets, evaluators, or interpreting the output of `lcagents eval run` and `lcagents eval compare`.
---

# lcagents Evals

Evals run via LangSmith. `LANGSMITH_API_KEY` must be set.

## Datasets

`evals/datasets/*.jsonl` — one JSON object per line:

    {"input": {"messages": [{"role": "user", "content": "..."}]}, "reference": "optional"}

`smoke.jsonl` is the 3-row gate that `lcagents deploy` runs as a pre-flight.

## Evaluators

`evals/evaluators.py` exports `EVALUATORS` — a list of LangSmith evaluator callables. Each takes `(run, example)` and returns `{"key": str, "score": float, "comment": str?}`.

## Running

- `lcagents eval run` — full
- `lcagents eval run --smoke` — smoke only
- `lcagents eval compare evals/results/A.json evals/results/B.json` — metric deltas

## Reading `compare`

Look at the `delta` column. `+` means metric went up. Whether that's good depends on the metric: `+` is good for `correctness`, bad for `latency`/`token_cost`.
```

- [ ] **Step 17.7: Author `lcagents-deploy.md`**

```markdown
---
name: lcagents-deploy
description: Use when preparing or executing a deploy — setting secrets, picking targets, smoke-testing.
---

# lcagents Deploy

## Targets

- `lcagents deploy langsmith` — pushes via `langgraph build/deploy` to LangSmith Cloud.
- `lcagents deploy docker --tag <name:tag>` — builds a self-contained image; optional `--push <registry>`.

Both run a smoke pre-flight. If smoke fails, **fix the agent or the smoke dataset; do not bypass**.

## Secrets

- `.env` is the source of truth; populated by `lcagents login`.
- LangSmith deploy pushes secrets to LangSmith via API.
- Docker deploy does **not** bake secrets into the image. The CLI prints the `docker run --env-file .env` invocation.
- **Never** print or display `.env` content.

## After deploy

LangSmith: open the printed trace URL.
Docker: `docker run --env-file .env -p 8080:8080 <tag>` then `curl localhost:8080/healthz`.
```

- [ ] **Step 17.8: Author `lcagents-observability.md`**

```markdown
---
name: lcagents-observability
description: Use when debugging an agent's behaviour, reading LangSmith traces, or setting up tracing in a fresh project.
---

# lcagents Observability

LangSmith tracing is on whenever `LANGSMITH_TRACING=true` is in `.env` (it's set by default in scaffolded projects).

## Where traces live

LangSmith UI -> `LANGSMITH_PROJECT` (defaults to the project name). Each `agent.invoke(...)` is one trace; tool calls and sub-agent delegations are nested spans.

## Common failure patterns

| Symptom | Likely cause |
|---|---|
| `agent` import fails | `agent/agent.py` doesn't export a symbol named `agent`, or imports broke |
| Smoke pre-flight fails | Provider key missing, model name typo, tool error |
| `langgraph dev` hangs | `langgraph.json` graph path wrong |
| Docker container crashes on boot | `.env` not passed at runtime |
```

- [ ] **Step 17.9: Add a regression test that all skills exist with frontmatter**

`tests/test_skills_present.py`:
```python
from importlib.resources import files
from pathlib import Path

EXPECTED = [
    "lcagents-workflow.md",
    "lcagents-scaffold.md",
    "lcagents-langgraph-code.md",
    "lcagents-deepagents-code.md",
    "lcagents-langchain-code.md",
    "lcagents-langsmith-evals.md",
    "lcagents-deploy.md",
    "lcagents-observability.md",
]


def test_all_global_skills_present_with_frontmatter() -> None:
    skills_dir = Path(str(files("lcagents") / "skills"))
    for name in EXPECTED:
        path = skills_dir / name
        assert path.is_file(), f"Missing skill: {name}"
        text = path.read_text("utf-8")
        assert text.startswith("---\n"), f"Missing frontmatter: {name}"
        assert "name:" in text and "description:" in text, f"Frontmatter incomplete: {name}"
```

- [ ] **Step 17.10: Run tests**

```bash
pytest -v
```
Expected: all green.

- [ ] **Step 17.11: Commit**

```bash
git add src/lcagents/skills tests/test_skills_present.py
git commit -m "docs(skills): author the 8 global skill files for coding agents"
```

---

## Task 18: End-to-end integration test

Scaffold each template, run `uv sync`, and confirm `ruff check` runs. Slow; gated behind a marker.

**Files:**
- Modify: `pyproject.toml` (add `integration` marker)
- Create: `tests/integration/__init__.py`
- Create: `tests/integration/test_e2e.py`

- [ ] **Step 18.1: Add the marker to `pyproject.toml`**

Append under `[tool.pytest.ini_options]`:
```toml
markers = ["integration: end-to-end tests that hit the network or build images"]
```

- [ ] **Step 18.2: Write the test**

`tests/integration/__init__.py`: empty.

`tests/integration/test_e2e.py`:
```python
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
    proc = subprocess.run(["uv", "sync"], cwd=project, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr

    proc = subprocess.run(
        [str(project / ".venv" / "bin" / "ruff"), "check", "."],
        cwd=project, capture_output=True, text=True,
    )
    # ruff may flag template-generated files; assert it ran
    assert proc.returncode in (0, 1)
```

- [ ] **Step 18.3: Run unit tests (skip integration by default)**

```bash
pytest -v -m "not integration"
```
Expected: all green; integration tests not collected.

- [ ] **Step 18.4: Run integration tests once locally to confirm they work**

```bash
pytest -v -m integration
```
Expected: 3 passed (slow — pulls real packages with `uv sync`).

- [ ] **Step 18.5: Commit**

```bash
git add pyproject.toml tests/integration
git commit -m "test: add integration tests for scaffold + install + lint per template"
```

---

## Task 19: Documentation polish + final manual smoke

**Files:**
- Modify: `README.md`

- [ ] **Step 19.1: Replace `README.md` with the user-facing version**

```markdown
# langchain-agents-cli (`lcagents`)

A tool *for* coding agents (Claude Code, Codex), not a coding agent itself. Scaffolds, runs, evaluates, and deploys LangChain / LangGraph / DeepAgents projects.

## Install

    uvx langchain-agents-cli setup
    # or, in a venv:
    pip install langchain-agents-cli && lcagents setup

`setup` installs the lcagents skills into Claude Code (`~/.claude/skills/`) and Codex (`~/.codex/skills/`) if found.

## Scaffold a project

    lcagents scaffold create my-agent --template langgraph-agent
    cd my-agent
    lcagents install
    lcagents login        # populate .env
    lcagents run "hello"

Templates:
- `langgraph-agent` — explicit StateGraph
- `deep-agent` — DeepAgents (planning + sub-agents + virtual FS)
- `langchain-chain` — LCEL chain (RAG / non-agentic)

## Other commands

| Command | What it does |
|---|---|
| `lcagents dev` | Interactive LangGraph dev server |
| `lcagents eval run` | LangSmith evals |
| `lcagents eval compare` | Diff two eval result files |
| `lcagents deploy langsmith` | Push to LangSmith Cloud |
| `lcagents deploy docker --tag X` | Build a self-contained image |
| `lcagents scaffold enhance --add docker` | Add deploy to an existing project |
| `lcagents scaffold upgrade` | Re-sync skills/templates after a CLI bump |

## Design

See `docs/superpowers/specs/2026-04-27-langchain-agents-cli-design.md`.

## License

Apache-2.0.
```

- [ ] **Step 19.2: Manual end-to-end smoke (do once by hand, not a test)**

```bash
cd /tmp
lcagents scaffold create demo --template langgraph-agent
cd demo
lcagents install
echo "OPENAI_API_KEY=sk-..." > .env
echo "LANGSMITH_API_KEY=ls-..." >> .env
echo "LANGSMITH_TRACING=true" >> .env
echo "LANGSMITH_PROJECT=demo" >> .env
lcagents run "Say hi in one word."
```
Expected: agent responds, trace appears in LangSmith.

- [ ] **Step 19.3: Commit**

```bash
git add README.md
git commit -m "docs: write user-facing README"
```

---

## Self-review

After all tasks complete:

- [ ] Re-read `docs/superpowers/specs/2026-04-27-langchain-agents-cli-design.md` and confirm every section in §5 (Command Surface), §7 (Layout), §8 (Skill Catalog), §10 (Eval), §11 (Deploy), §12 (enhance/upgrade) maps to a task above.
- [ ] Run `pytest -v -m "not integration"` and confirm all green.
- [ ] Run `lcagents info` outside a project and inside a scaffolded project; both should print sensible output.
- [ ] Run `ruff check src/` and `mypy src/lcagents` on this CLI's own source. Fix any drift.

## Out-of-scope reminders (do NOT implement)

Per spec §3: Cursor / Gemini CLI / Antigravity skill installation, Cloud Run / Lambda / K8s deploy targets, RAG ingestion command, multi-project monorepos, TUI/REPL.
