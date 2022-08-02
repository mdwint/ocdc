import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pytest

from ocdc.__main__ import DEFAULT_PATH, main

data_dir = Path(__file__).parent.parent / "data"
src_path = data_dir / "basic.in.md"


@pytest.fixture()
def tmp_path(chdir):
    with TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir, DEFAULT_PATH)
        shutil.copyfile(src_path, tmp_path)
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
    assert err == f"ERROR: {tmp_path.name} would be reformatted"


def test_new_exists(tmp_path):
    with pytest.raises(SystemExit) as excinfo:
        ocdc("new")

    err = excinfo.value.code
    assert err == f"ERROR: {tmp_path.name} exists (use --force to overwrite)"


def test_new_force(tmp_path):
    ocdc("new", "--force")
