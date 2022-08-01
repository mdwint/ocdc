from pathlib import Path

import pytest

from ocdc.parser import ParseError, ast, parse

data_dir = Path(__file__).parent.parent / "data"
text_paths = sorted(data_dir.glob("*.in.md"))


@pytest.mark.parametrize("text_path", text_paths, ids=[str(p) for p in text_paths])
def test_parse(text_path, dump_expected_output):
    text = text_path.read_text()

    actual_ast = parse(text)
    a = actual_ast.json(indent=2, exclude_defaults=True)

    ast_path = Path(str(text_path).split(".", 1)[0] + ".ast.json")
    if dump_expected_output:
        dump_expected_output(ast_path, a + "\n")

    expected_ast = ast.Changelog.parse_file(ast_path)
    b = expected_ast.json(indent=2, exclude_defaults=True)

    assert a == b


def test_parse_error_unexpected_title_for_changes():
    text = (data_dir / "unexpected_title_for_changes.err.md").read_text()

    with pytest.raises(ParseError) as excinfo:
        parse(text)

    expected_error = """
Unexpected title for changes (line 11, column 5):

  ### Oops
      ^^^^
""".strip()
    assert str(excinfo.value) == expected_error


def test_parse_error_unprocessable_text():
    text = (data_dir / "unprocessable_text.err.md").read_text()

    with pytest.raises(ParseError) as excinfo:
        parse(text)

    expected_error = """
Unprocessable text (line 10, column 3):

  - The first version.
    #### This trailing text cannot be parsed
    ^
""".strip()
    assert str(excinfo.value) == expected_error
