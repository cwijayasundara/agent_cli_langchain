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
