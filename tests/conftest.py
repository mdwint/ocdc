import os
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Optional

import pytest

DUMP_EXPECTED_OUTPUTS = "--dump-expected-outputs"


def pytest_addoption(parser):
    g = parser.getgroup("ocdc")
    g.addoption(
        DUMP_EXPECTED_OUTPUTS,
        action="store_true",
        help="Dump expected outputs of test cases",
    )


@pytest.fixture(scope="session")
def dump_expected_output(request) -> Optional[Callable[[Path, str], None]]:
    if request.config.getoption(DUMP_EXPECTED_OUTPUTS):

        def dump(path: Path, text: str) -> None:
            path.write_text(text)
            pytest.skip()

        return dump
    return None


@pytest.fixture(scope="session")
def chdir():
    @contextmanager
    def _chdir(path):
        orig = os.getcwd()
        os.chdir(path)
        try:
            yield
        finally:
            os.chdir(orig)

    return _chdir
