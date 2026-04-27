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
