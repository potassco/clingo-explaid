"""
Test cases for main application functionality.
"""

from pathlib import Path
from unittest import TestCase

TEST_DIR = parent = Path(__file__).resolve().parent


def read_file(path: str | Path, encoding: str = "utf-8") -> str:
    """
    Read file at path and return contents as string.
    """
    with open(path, encoding=encoding) as f:
        return f.read()


class TestMain(TestCase):
    """
    Test cases for clingexplaid.
    """
