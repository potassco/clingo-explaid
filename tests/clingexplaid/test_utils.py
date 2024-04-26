"""
Tests for the utils package
"""

from unittest import TestCase

from clingexplaid.utils import get_constants_from_arguments, get_signatures_from_model_string


class TestUtils(TestCase):
    """
    Test cases for clingexplaid.
    """

    def test_get_signatures_from_model_string(self) -> None:
        """
        Test getting signatures from a model string.
        """
        model_string = "a(1,2) a(1,5) a(3,5) a(1,2,3) a(1,3,5), foo(bar), zero"
        signatures = get_signatures_from_model_string(model_string)
        self.assertEqual(signatures, {("a", 2), ("a", 3), ("foo", 1), ("zero", 0)})

    def test_get_constants_from_arguments(self) -> None:
        """
        Test getting constants from argument vector.
        """
        self.assertEqual(get_constants_from_arguments(["-c", "a=42"]), {"a": "42"})
        self.assertEqual(get_constants_from_arguments(["test/dir/file.lp", "--const", "blob=value"]), {"blob": "value"})
        self.assertEqual(get_constants_from_arguments(["--const", "-a", "test/42"]), {})
