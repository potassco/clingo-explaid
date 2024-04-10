"""
Test cases for main application functionality.
"""

import random
from pathlib import Path
from typing import List, Optional, Set, Tuple, Union
from unittest import TestCase

import clingo

from clingexplaid.utils import AssumptionSet
from clingexplaid.muc import CoreComputer
from clingexplaid.transformers import (
    AssumptionTransformer,
    ConstraintTransformer,
    RuleIDTransformer,
    RuleSplitter,
)
from clingexplaid.transformers.exceptions import UntransformedException


TEST_DIR = parent = Path(__file__).resolve().parent


class TestMain(TestCase):
    """
    Test cases for clingexplaid.
    """

    @staticmethod
    def read_file(path: Union[str, Path], encoding: str = "utf-8") -> str:
        """
        Read file at path and return contents as string.
        """
        with open(path, "r", encoding=encoding) as f:
            return f.read()

    @staticmethod
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

    def assert_muc(
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

    # TRANSFORMERS
    # --- ASSUMPTION TRANSFORMER

    def test_assumption_transformer_parse_file(self) -> None:
        """
        Test the AssumptionTransformer's `parse_file` method.
        """
        program_path = TEST_DIR.joinpath("res/test_program.lp")
        program_path_transformed = TEST_DIR.joinpath("res/transformed_program_assumptions_certain_signatures.lp")
        at = AssumptionTransformer(signatures={(c, 1) for c in "abcdef"})
        result = at.parse_files([program_path])
        self.assertEqual(result.strip(), self.read_file(program_path_transformed).strip())

    def test_assumption_transformer_parse_file_no_signatures(self) -> None:
        """
        Test the AssumptionTransformer's `parse_file` method with no signatures provided.
        """
        program_path = TEST_DIR.joinpath("res/test_program.lp")
        program_path_transformed = TEST_DIR.joinpath("res/transformed_program_assumptions_all.lp")
        at = AssumptionTransformer()
        result = at.parse_files([program_path])
        self.assertEqual(result.strip(), self.read_file(program_path_transformed).strip())

    def test_assumption_transformer_get_assumptions_before_transformation(self) -> None:
        """
        Test the AssumptionTransformer's behavior when get_assumptions is called before transformation.
        """
        at = AssumptionTransformer()
        control = clingo.Control()
        self.assertRaises(UntransformedException, lambda: at.get_assumptions(control))

    # --- RULE ID TRANSFORMER

    def test_rule_id_transformer(self) -> None:
        """
        Test the RuleIDTransformer's `parse_file` and `get_assumptions` methods.
        """
        program_path = TEST_DIR.joinpath("res/test_program.lp")
        program_path_transformed = TEST_DIR.joinpath("res/transformed_program_rule_ids.lp")
        rt = RuleIDTransformer()
        result = rt.parse_file(program_path)
        self.assertEqual(result.strip(), self.read_file(program_path_transformed).strip())
        assumptions = {
            (clingo.parse_term(s), True)
            for s in [
                "_rule(1)",
                "_rule(2)",
                "_rule(3)",
                "_rule(4)",
                "_rule(5)",
                "_rule(6)",
                "_rule(7)",
            ]
        }
        self.assertEqual(assumptions, rt.get_assumptions())

    # --- CONSTRAINT TRANSFORMER

    def test_constraint_transformer(self) -> None:
        """
        Test the ConstraintTransformer's `parse_file` method.
        """
        program_path = TEST_DIR.joinpath("res/test_program_constraints.lp")
        program_path_transformed = TEST_DIR.joinpath("res/transformed_program_constraints.lp")
        ct = ConstraintTransformer(constraint_head_symbol="unsat")
        result = ct.parse_files([program_path])
        self.assertEqual(result.strip(), self.read_file(program_path_transformed).strip())

    # --- RULE SPLITTER

    def test_rule_splitter(self) -> None:
        """
        Test the RuleSplitter's `parse_file` method.
        """

        program_path = TEST_DIR.joinpath("res/test_program_rules.lp")
        program_path_transformed = TEST_DIR.joinpath("res/transformed_program_rules_split.lp")
        rs = RuleSplitter()
        result = rs.parse_file(program_path)
        self.assertEqual(result.strip(), self.read_file(program_path_transformed).strip())

    # MUC

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

        muc, cc = self.get_muc_of_program(program_string=program, assumption_signatures=signatures, control=ctl)

        if cc.minimal is None:
            self.fail()
        self.assert_muc(cc.muc_to_string(muc), [{"a(1)", "a(4)", "a(5)"}])

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

        muc, cc = self.get_muc_of_program(program_string=program, assumption_signatures=signatures, control=ctl)

        if cc.minimal is None:
            self.fail()
        self.assert_muc(cc.muc_to_string(muc), [{"a(3)"}])

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

        muc, cc = self.get_muc_of_program(program_string=program, assumption_signatures=signatures, control=ctl)

        if cc.minimal is None:
            self.fail()
        self.assert_muc(cc.muc_to_string(muc), [{"a(3)"}, {"a(5)"}, {"a(9)"}])

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

        muc, cc = self.get_muc_of_program(program_string=program, assumption_signatures=signatures, control=ctl)

        if cc.minimal is None:
            self.fail()
        self.assert_muc(
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

        muc, cc = self.get_muc_of_program(program_string=program, assumption_signatures=signatures, control=ctl)

        if cc.minimal is None:
            self.fail()
        self.assert_muc(cc.muc_to_string(muc), [{f"a({i})" for i in random_core}])

    def test_core_computer_shrink_satisfiable(self) -> None:
        """
        Test the CoreComputer's `shrink` function with a satisfiable assumption set.
        """

        ctl = clingo.Control()

        program = """
        a(1..5).
        """
        signatures = {("a", 1)}

        muc, _ = self.get_muc_of_program(program_string=program, assumption_signatures=signatures, control=ctl)

        self.assertEqual(muc, set())

    # --- INTERNAL

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
