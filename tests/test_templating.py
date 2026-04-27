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
