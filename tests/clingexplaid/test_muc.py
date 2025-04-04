"""
Tests for the mus package
"""

import random
from typing import Iterable, List, Optional, Sequence, Set, Tuple, Union
from unittest import TestCase

import clingo

from clingexplaid.mus import CoreComputer
from clingexplaid.transformers import AssumptionTransformer
from clingexplaid.transformers.transformer_assumption import FilterPattern, FilterSignature
from clingexplaid.utils.types import AssumptionSet

from .test_main import TEST_DIR


def get_mus_of_program(
    program_string: str,
    assumption_filters: Optional[Iterable[Union[FilterPattern, FilterSignature]]] = None,
    control: Optional[clingo.Control] = None,
) -> Tuple[AssumptionSet, CoreComputer]:
    """
    Helper function to directly get the MUS of a given program string.
    """

    if assumption_filters is None:
        assumption_filters = set()
    else:
        assumption_filters = set(assumption_filters)

    ctl = control if control is not None else clingo.Control()

    at = AssumptionTransformer(filters=assumption_filters)
    transformed_program = at.parse_string(program_string)

    ctl.add("base", [], transformed_program)
    ctl.ground([("base", [])])

    assumptions = at.get_assumption_literals(ctl)

    cc = CoreComputer(ctl, assumptions)

    def shrink_on_model(core: Sequence[int]) -> None:
        _ = cc.shrink(core)

    ctl.solve(assumptions=list(assumptions), on_core=shrink_on_model)

    # if the instance was satisfiable and the on_core function wasn't called an empty set is returned, else the mus.
    result = cc.minimal if cc.minimal is not None else set()

    return result, cc


class TestMUS(TestCase):
    """
    Test cases for MUS functionality.
    """

    def _assert_mus(
        self,
        mus: Set[str],
        valid_mus_string_lists: List[Set[str]],
    ) -> None:
        """
        Asserts if a MUS is one of several valid MUS's.
        """
        valid_mus_list = [{clingo.parse_term(s) for s in lit_strings} for lit_strings in valid_mus_string_lists]
        parsed_mus = {clingo.parse_term(s) for s in mus}
        self.assertIn(parsed_mus, valid_mus_list)

    def test_core_computer_shrink_single_mus(self) -> None:
        """
        Test the CoreComputer's `shrink` function with a single MUS.
        """

        ctl = clingo.Control()

        program = """
            a(1..5).
            :- a(1), a(4), a(5).
            """
        filters = {FilterSignature("a", 1)}

        mus, cc = get_mus_of_program(program_string=program, assumption_filters=filters, control=ctl)

        if cc.minimal is None:
            self.fail()
        self._assert_mus(cc.mus_to_string(mus), [{"a(1)", "a(4)", "a(5)"}])

    def test_core_computer_shrink_single_atomic_mus(self) -> None:
        """
        Test the CoreComputer's `shrink` function with a single atomic MUS.
        """

        ctl = clingo.Control()

        program = """
            a(1..5).
            :- a(3).
            """
        filters = {FilterSignature("a", 1)}

        mus, cc = get_mus_of_program(program_string=program, assumption_filters=filters, control=ctl)

        if cc.minimal is None:
            self.fail()
        self._assert_mus(cc.mus_to_string(mus), [{"a(3)"}])

    def test_core_computer_shrink_multiple_atomic_mus(self) -> None:
        """
        Test the CoreComputer's `shrink` function with multiple atomic MUS's.
        """

        ctl = clingo.Control()

        program = """
            a(1..10).
            :- a(3).
            :- a(5).
            :- a(9).
            """
        filters = {FilterSignature("a", 1)}

        mus, cc = get_mus_of_program(program_string=program, assumption_filters=filters, control=ctl)

        if cc.minimal is None:
            self.fail()
        self._assert_mus(cc.mus_to_string(mus), [{"a(3)"}, {"a(5)"}, {"a(9)"}])

    def test_core_computer_shrink_multiple_mus(self) -> None:
        """
        Test the CoreComputer's `shrink` function with multiple MUS's.
        """

        ctl = clingo.Control()

        program = """
            a(1..10).
            :- a(3), a(9), a(5).
            :- a(5), a(1), a(2).
            :- a(9), a(2), a(7).
            """
        filters = {FilterSignature("a", 1)}

        mus, cc = get_mus_of_program(program_string=program, assumption_filters=filters, control=ctl)

        if cc.minimal is None:
            self.fail()
        self._assert_mus(
            cc.mus_to_string(mus),
            [
                {"a(3)", "a(9)", "a(5)"},
                {"a(5)", "a(1)", "a(2)"},
                {"a(9)", "a(2)", "a(7)"},
            ],
        )

    def test_core_computer_shrink_large_instance_random(self) -> None:
        """
        Test the CoreComputer's `shrink` function with a large random assumption set.
        """

        ctl = clingo.Control()

        n_assumptions = 1000
        random_core = random.choices(range(1, n_assumptions), k=10)
        program = f"""
            a(1..{n_assumptions}).
            :- {', '.join([f"a({i})" for i in random_core])}.
            """
        filters = {FilterSignature("a", 1)}

        mus, cc = get_mus_of_program(program_string=program, assumption_filters=filters, control=ctl)

        if cc.minimal is None:
            self.fail()
        self._assert_mus(cc.mus_to_string(mus), [{f"a({i})" for i in random_core}])

    def test_core_computer_shrink_satisfiable(self) -> None:
        """
        Test the CoreComputer's `shrink` function with a satisfiable assumption set.
        """

        ctl = clingo.Control()

        program = """
            a(1..5).
            """
        filters = {FilterSignature("a", 1)}

        mus, _ = get_mus_of_program(program_string=program, assumption_filters=filters, control=ctl)

        self.assertEqual(mus, set())

    def test_core_computer_get_multiple_minimal(self) -> None:
        """
        Test the CoreComputer's `get_multiple_minimal` function to get multiple MUS's.
        """

        ctl = clingo.Control()

        program_path = TEST_DIR.joinpath("res/test_program_multi_mus.lp")
        at = AssumptionTransformer(filters={FilterSignature("a", 1)})
        parsed = at.parse_files([program_path])
        ctl.add("base", [], parsed)
        ctl.ground([("base", [])])
        cc = CoreComputer(ctl, at.get_assumption_literals(ctl))

        mus_generator = cc.get_multiple_minimal()

        mus_string_sets = [cc.mus_to_string(mus) for mus in list(mus_generator)]
        for mus_string_set in mus_string_sets:
            self.assertIn(
                mus_string_set,
                [{"a(1)", "a(2)"}, {"a(1)", "a(9)"}, {"a(3)", "a(5)", "a(8)"}],
            )

    def test_core_computer_get_multiple_minimal_max_mus_2(self) -> None:
        """
        Test the CoreComputer's `get_multiple_minimal` function to get multiple MUS's.
        """

        ctl = clingo.Control()

        program_path = TEST_DIR.joinpath("res/test_program_multi_mus.lp")
        at = AssumptionTransformer(filters={FilterSignature("a", 1)})
        parsed = at.parse_files([program_path])
        ctl.add("base", [], parsed)
        ctl.ground([("base", [])])
        cc = CoreComputer(ctl, at.get_assumption_literals(ctl))

        mus_generator = cc.get_multiple_minimal(max_mus=2)

        mus_string_sets = [cc.mus_to_string(mus) for mus in list(mus_generator)]
        for mus_string_set in mus_string_sets:
            self.assertIn(
                mus_string_set,
                [{"a(1)", "a(2)"}, {"a(1)", "a(9)"}, {"a(3)", "a(5)", "a(8)"}],
            )

        self.assertEqual(len(mus_string_sets), 2)

    # INTERNAL

    def test_core_computer_internal_solve_no_assumptions(self) -> None:
        """
        Test the CoreComputer's `_solve` function with no assumptions.
        """

        control = clingo.Control()
        cc = CoreComputer(control, set())
        satisfiable, _, _ = cc._solve()  # pylint: disable=W0212
        self.assertTrue(satisfiable)

    def test_core_computer_internal_compute_single_minimal_satisfiable(self) -> None:
        """
        Test the CoreComputer's `_compute_single_minimal` function with a satisfiable assumption set.
        """

        control = clingo.Control()
        program = "a.b.c."
        control.add("base", [], program)
        control.ground([("base", [])])
        assumptions = {(clingo.parse_term(c), True) for c in "abc"}
        cc = CoreComputer(control, assumptions)
        mus = cc._compute_single_minimal()  # pylint: disable=W0212
        self.assertEqual(mus, set())

    def test_core_computer_internal_compute_single_minimal_no_assumptions(self) -> None:
        """
        Test the CoreComputer's `_compute_single_minimal` function with no assumptions.
        """

        control = clingo.Control()
        cc = CoreComputer(control, set())
        # Disabled exception assertion due to change in error handling
        # self.assertRaises(ValueError, cc._compute_single_minimal)  # pylint: disable=W0212
        cc.shrink([])

    def test_core_computer_mus_to_string(self) -> None:
        """
        Test the CoreComputer's `_compute_single_minimal` function with no assumptions.
        """

        control = clingo.Control()
        cc = CoreComputer(control, set())
        self.assertEqual(
            cc.mus_to_string({(clingo.parse_term(string), True) for string in ["this", "is", "a", "test"]}),
            {"this", "is", "a", "test"},
        )  # pylint: disable=W0212
