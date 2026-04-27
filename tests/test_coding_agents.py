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
