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
