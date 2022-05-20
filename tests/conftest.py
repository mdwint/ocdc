import os
from contextlib import contextmanager

import pytest


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
