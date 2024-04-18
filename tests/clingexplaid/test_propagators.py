"""
Tests for the propagators package
"""

from unittest import TestCase

import clingo
from clingexplaid.propagators import DecisionOrderPropagator

from .test_main import TEST_DIR


class TestPropagators(TestCase):
    """
    Test cases for propagators.
    """

    # DECISION ORDER PROPAGATOR

    def test_decision_order_propagator(self) -> None:
        """
        Testing the functionality of the DecisionOrderPropagator without signatures
        """
        program_path = TEST_DIR.joinpath("res/test_program_decision_order.lp")
        control = clingo.Control()
        dop = DecisionOrderPropagator()
        control.register_propagator(dop)  # type: ignore
        control.load(str(program_path))
        control.ground()
        control.solve(assumptions=[])

        # No asserts since the propagator currently doesn't support any outputs but only prints.

    def test_decision_order_propagator_with_signatures(self) -> None:
        """
        Testing the functionality of the DecisionOrderPropagator with signatures
        """
        program_path = TEST_DIR.joinpath("res/test_program_decision_order.lp")
        control = clingo.Control()
        dop = DecisionOrderPropagator(signatures={("a", 0), ("b", 0), ("x", 1)})
        control.register_propagator(dop)  # type: ignore
        control.load(str(program_path))
        control.ground()
        control.solve(assumptions=[])

        # No asserts since the propagator currently doesn't support any outputs but only prints.
