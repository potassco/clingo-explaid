"""
Test cases for main application functionality.
"""

from unittest import TestCase
from clingexplaid.utils.transformer import AssumptionTransformer


class TestMain(TestCase):
    """
    Test cases for clingexplaid.
    """

    def test_assumption_transformer_parse_string(self):
        program = """
            a(1).
            a(2) :- x.
            a(3); a(4) :- x.
            a(10..15).
            a(16).
            a(17); a(18) :- a(16).
        """
        program_transformed = """
            {a(1)}.
            a(2) :- x.
            a(3); a(4) :- x.
            {a(10..15)}.
            {a(16)}.
            a(17); a(18) :- a(16).
        """
        at = AssumptionTransformer(signatures=[('a', 1)])
        result = at.parse_string(program)
        self.assertEqual(result, program_transformed)
