import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pytest

from ocdc.__main__ import DEFAULT_PATH, main

data_dir = Path(__file__).parent.parent / "data"
src_path = data_dir / "basic.in.md"
src_path_err = data_dir / "duplicate_version_sections.err.md"


@pytest.fixture()
def tmp_path(chdir):
    with TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir, DEFAULT_PATH)
        shutil.copyfile(src_path, tmp_path)
        other_file = tmp_path.parent / "other_dir" / "INVALID_CHANGELOG.md"
        other_file.parent.mkdir(exist_ok=True, parents=True)
        shutil.copyfile(src_path_err, other_file)
        with chdir(tmp_dir):
            yield tmp_path


def ocdc(*args: str):
    with patch("sys.argv", ["ocdc", *args]):
        main()


def test_format(tmp_path):
    ocdc()


def test_format_path(tmp_path):
    ocdc("--path", str(tmp_path.parent))


def test_format_read_stdin():
    with patch("sys.stdin.read", src_path.read_text):
        ocdc("--path", "-")


def test_check(tmp_path):
    with pytest.raises(SystemExit) as excinfo:
        ocdc("--check")

    err = excinfo.value.code
    assert err == f"ERROR: {tmp_path.name}: would be reformatted"


def test_new_exists(tmp_path):
    with pytest.raises(SystemExit) as excinfo:
        ocdc("new")

    err = excinfo.value.code
    assert err == f"ERROR: {tmp_path.name} exists (use --force to overwrite)"


def test_new_force(tmp_path):
    ocdc("new", "--force")


def test_batch_format(tmp_path: Path):
    with pytest.raises(SystemExit) as excinfo:
        ocdc(
            "-p",
            "CHANGELOG.md",
            "other_dir/INVALID_CHANGELOG.md",
            "this_file_does_not_exist.md",
        )
    err = excinfo.value.code
    assert err == "ERROR: 2 file(s) were invalid"


def test_batch_format_check(tmp_path: Path):
    with pytest.raises(SystemExit) as excinfo:
        ocdc(
            "--check",
            "-p",
            "CHANGELOG.md",
            "other_dir/INVALID_CHANGELOG.md",
            "this_file_does_not_exist.md",
        )
    err = excinfo.value.code
    assert err == "ERROR: 3 file(s) were invalid or would be reformatted"
