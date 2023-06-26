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
            fact.
        """
        at = AssumptionTransformer(signatures=[('fact', 0)])
        result = at.parse_string(program)
        self.assertEqual(result, "{fact}.")
