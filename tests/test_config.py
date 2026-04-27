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
