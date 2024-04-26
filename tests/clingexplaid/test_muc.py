"""
Tests for the muc package
"""

import random
from typing import List, Optional, Set, Tuple
from unittest import TestCase

import clingo

from clingexplaid.muc import CoreComputer
from clingexplaid.transformers import AssumptionTransformer
from clingexplaid.utils.types import AssumptionSet

from .test_main import TEST_DIR


def get_muc_of_program(
    program_string: str,
    assumption_signatures: Set[Tuple[str, int]],
    control: Optional[clingo.Control] = None,
) -> Tuple[AssumptionSet, CoreComputer]:
    """
    Helper function to directly get the MUC of a given program string.
    """
    ctl = control if control is not None else clingo.Control()

    at = AssumptionTransformer(signatures=assumption_signatures)
    transformed_program = at.parse_string(program_string)

    ctl.add("base", [], transformed_program)
    ctl.ground([("base", [])])

    assumptions = at.get_assumptions(ctl)

    cc = CoreComputer(ctl, assumptions)
    ctl.solve(assumptions=list(assumptions), on_core=cc.shrink)

    # if the instance was satisfiable and the on_core function wasn't called an empty set is returned, else the muc.
    result = cc.minimal if cc.minimal is not None else set()

    return result, cc


class TestMUC(TestCase):
    """
    Test cases for MUC functionality.
    """

    def _assert_muc(
        self,
        muc: Set[str],
        valid_mucs_string_lists: List[Set[str]],
    ) -> None:
        """
        Asserts if a MUC is one of several valid MUC's.
        """
        valid_mucs = [{clingo.parse_term(s) for s in lit_strings} for lit_strings in valid_mucs_string_lists]
        parsed_muc = {clingo.parse_term(s) for s in muc}
        self.assertIn(parsed_muc, valid_mucs)

    def test_core_computer_shrink_single_muc(self) -> None:
        """
        Test the CoreComputer's `shrink` function with a single MUC.
        """

        ctl = clingo.Control()

        program = """
            a(1..5).
            :- a(1), a(4), a(5).
            """
        signatures = {("a", 1)}

        muc, cc = get_muc_of_program(program_string=program, assumption_signatures=signatures, control=ctl)

        if cc.minimal is None:
            self.fail()
        self._assert_muc(cc.muc_to_string(muc), [{"a(1)", "a(4)", "a(5)"}])

    def test_core_computer_shrink_single_atomic_muc(self) -> None:
        """
        Test the CoreComputer's `shrink` function with a single atomic MUC.
        """

        ctl = clingo.Control()

        program = """
            a(1..5).
            :- a(3).
            """
        signatures = {("a", 1)}

        muc, cc = get_muc_of_program(program_string=program, assumption_signatures=signatures, control=ctl)

        if cc.minimal is None:
            self.fail()
        self._assert_muc(cc.muc_to_string(muc), [{"a(3)"}])

    def test_core_computer_shrink_multiple_atomic_mucs(self) -> None:
        """
        Test the CoreComputer's `shrink` function with multiple atomic MUC's.
        """

        ctl = clingo.Control()

        program = """
            a(1..10).
            :- a(3).
            :- a(5).
            :- a(9).
            """
        signatures = {("a", 1)}

        muc, cc = get_muc_of_program(program_string=program, assumption_signatures=signatures, control=ctl)

        if cc.minimal is None:
            self.fail()
        self._assert_muc(cc.muc_to_string(muc), [{"a(3)"}, {"a(5)"}, {"a(9)"}])

    def test_core_computer_shrink_multiple_mucs(self) -> None:
        """
        Test the CoreComputer's `shrink` function with multiple MUC's.
        """

        ctl = clingo.Control()

        program = """
            a(1..10).
            :- a(3), a(9), a(5).
            :- a(5), a(1), a(2).
            :- a(9), a(2), a(7).
            """
        signatures = {("a", 1)}

        muc, cc = get_muc_of_program(program_string=program, assumption_signatures=signatures, control=ctl)

        if cc.minimal is None:
            self.fail()
        self._assert_muc(
            cc.muc_to_string(muc),
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
        random_core = random.choices(range(n_assumptions), k=10)
        program = f"""
            a(1..{n_assumptions}).
            :- {', '.join([f"a({i})" for i in random_core])}.
            """
        signatures = {("a", 1)}

        muc, cc = get_muc_of_program(program_string=program, assumption_signatures=signatures, control=ctl)

        if cc.minimal is None:
            self.fail()
        self._assert_muc(cc.muc_to_string(muc), [{f"a({i})" for i in random_core}])

    def test_core_computer_shrink_satisfiable(self) -> None:
        """
        Test the CoreComputer's `shrink` function with a satisfiable assumption set.
        """

        ctl = clingo.Control()

        program = """
            a(1..5).
            """
        signatures = {("a", 1)}

        muc, _ = get_muc_of_program(program_string=program, assumption_signatures=signatures, control=ctl)

        self.assertEqual(muc, set())

    def test_core_computer_get_multiple_minimal(self) -> None:
        """
        Test the CoreComputer's `get_multiple_minimal` function to get multiple MUCs.
        """

        ctl = clingo.Control()

        program_path = TEST_DIR.joinpath("res/test_program_multi_muc.lp")
        at = AssumptionTransformer(signatures={("a", 1)})
        parsed = at.parse_files([program_path])
        ctl.add("base", [], parsed)
        ctl.ground([("base", [])])
        cc = CoreComputer(ctl, at.get_assumptions(ctl))

        muc_generator = cc.get_multiple_minimal()

        muc_string_sets = [cc.muc_to_string(muc) for muc in list(muc_generator)]
        for muc_string_set in muc_string_sets:
            self.assertIn(
                muc_string_set,
                [{"a(1)", "a(2)"}, {"a(1)", "a(9)"}, {"a(3)", "a(5)", "a(8)"}],
            )

    def test_core_computer_get_multiple_minimal_max_mucs_2(self) -> None:
        """
        Test the CoreComputer's `get_multiple_minimal` function to get multiple MUCs.
        """

        ctl = clingo.Control()

        program_path = TEST_DIR.joinpath("res/test_program_multi_muc.lp")
        at = AssumptionTransformer(signatures={("a", 1)})
        parsed = at.parse_files([program_path])
        ctl.add("base", [], parsed)
        ctl.ground([("base", [])])
        cc = CoreComputer(ctl, at.get_assumptions(ctl))

        muc_generator = cc.get_multiple_minimal(max_mucs=2)

        muc_string_sets = [cc.muc_to_string(muc) for muc in list(muc_generator)]
        for muc_string_set in muc_string_sets:
            self.assertIn(
                muc_string_set,
                [{"a(1)", "a(2)"}, {"a(1)", "a(9)"}, {"a(3)", "a(5)", "a(8)"}],
            )

        self.assertEqual(len(muc_string_sets), 2)

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
        muc = cc._compute_single_minimal()  # pylint: disable=W0212
        self.assertEqual(muc, set())

    def test_core_computer_internal_compute_single_minimal_no_assumptions(self) -> None:
        """
        Test the CoreComputer's `_compute_single_minimal` function with no assumptions.
        """

        control = clingo.Control()
        cc = CoreComputer(control, set())
        self.assertRaises(ValueError, cc._compute_single_minimal)  # pylint: disable=W0212

    def test_core_computer_muc_to_string(self) -> None:
        """
        Test the CoreComputer's `_compute_single_minimal` function with no assumptions.
        """

        control = clingo.Control()
        cc = CoreComputer(control, set())
        self.assertEqual(
            cc.muc_to_string({(clingo.parse_term(string), True) for string in ["this", "is", "a", "test"]}),
            {"this", "is", "a", "test"},
        )  # pylint: disable=W0212
