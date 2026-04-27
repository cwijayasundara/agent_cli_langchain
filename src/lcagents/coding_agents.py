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
