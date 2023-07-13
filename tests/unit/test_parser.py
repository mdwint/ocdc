from pathlib import Path

import pytest

from ocdc.parser import ParseError, ast, parse

data_dir = Path(__file__).parent.parent / "data"


def with_paths(pattern: str):
    paths = sorted(data_dir.glob(pattern))
    return pytest.mark.parametrize("text_path", paths, ids=[p.name for p in paths])


@with_paths("*.in.md")
def test_parse(text_path, dump_expected_output):
    text = text_path.read_text()

    actual_ast = parse(text)
    a = actual_ast.model_dump_json(indent=2, exclude_defaults=True)

    ast_path = Path(str(text_path).split(".", 1)[0] + ".ast.json")
    if dump_expected_output:
        dump_expected_output(ast_path, a + "\n")

    expected_ast = ast.Changelog.model_validate_json(ast_path.read_text())
    b = expected_ast.model_dump_json(indent=2, exclude_defaults=True)

    assert a == b


@with_paths("*.err.md")
def test_parse_error(text_path, dump_expected_output):
    text = text_path.read_text()

    with pytest.raises(ParseError) as excinfo:
        parse(text)
    actual_error = str(excinfo.value)

    error_path = Path(str(text_path).split(".", 1)[0] + ".err.txt")
    if dump_expected_output:
        dump_expected_output(error_path, actual_error + "\n")

    expected_error = error_path.read_text().strip()
    assert actual_error == expected_error
