"""3-way merge for `lcagents scaffold upgrade`.

Strategy:
- Snapshot of originally-rendered files lives at `.agents/baseline/`.
  Created lazily on first upgrade if missing — older projects then assume
  "user content == baseline", which means non-edited files upgrade cleanly.
- For each tracked file:
    base    = baseline content
    current = file in project today
    new     = freshly-rendered template content
  - current is None (deleted)  → write new, mark updated
  - base == current            → overwrite with new (clean upgrade), or no-op if new==current
  - new == current             → no change
  - all three differ           → write <file>.lcagents-upgrade.txt conflict file; leave current
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
    """Return all files under root matching the tracked relative paths."""
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
    """Apply a 3-way merge upgrade to the project.

    Returns:
        (updated_paths, conflict_paths)
    """
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
            # If no baseline exists yet, treat baseline == current so non-edited
            # files upgrade cleanly (first-ever upgrade on an existing project).
            base_text = base.read_text("utf-8") if base.exists() else cur_text

            if cur_text is None:
                # File was deleted — adopt the new template content.
                current.parent.mkdir(parents=True, exist_ok=True)
                current.write_text(new_text, "utf-8")
                updated.append(current)
                continue

            if cur_text == base_text:
                # User hasn't touched this file.
                if cur_text != new_text:
                    current.write_text(new_text, "utf-8")
                    updated.append(current)
                # else: no change needed
                continue

            if new_text == cur_text:
                # User's edits happen to match the new template — nothing to do.
                continue

            # All three differ: user edited AND template changed → conflict.
            conflict_path = current.with_suffix(current.suffix + ".lcagents-upgrade.txt")
            header = (
                "# Conflict from `lcagents scaffold upgrade`\n"
                f"# Your file at {rel} was modified.\n"
                "# Below is the new template content. Merge manually and delete this file.\n\n"
            )
            conflict_path.write_text(header + new_text, "utf-8")
            conflicts.append(conflict_path)

        # Refresh the baseline snapshot with the freshly-rendered content.
        if baseline_root.exists():
            shutil.rmtree(baseline_root)
        for fresh_file in _walk(fresh, TRACKED):
            rel = fresh_file.relative_to(fresh)
            target = baseline_root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(fresh_file, target)

    save_config(project_root, replace(cfg, scaffolder_version=__version__))
    return updated, conflicts
