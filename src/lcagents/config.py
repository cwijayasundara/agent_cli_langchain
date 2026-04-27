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
