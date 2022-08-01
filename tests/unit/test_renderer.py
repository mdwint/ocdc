from pathlib import Path

import pytest

from ocdc.parser import ast
from ocdc.renderer import render_markdown, render_new_template

data_dir = Path(__file__).parent.parent / "data"
text_paths = sorted(data_dir.glob("*.out.md"))


@pytest.mark.parametrize("text_path", text_paths, ids=[str(p) for p in text_paths])
def test_render_markdown(text_path, dump_expected_output):
    ast_path = Path(str(text_path).split(".", 1)[0] + ".ast.json")
    changelog = ast.Changelog.parse_file(ast_path)

    actual_text = render_markdown(changelog)

    if dump_expected_output:
        dump_expected_output(text_path, actual_text)

    expected_text = text_path.read_text()
    assert actual_text == expected_text


def test_render_new_template():
    render_new_template()
