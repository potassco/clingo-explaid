"""
Test cases for main application functionality.
"""

from unittest import TestCase
from clingexplaid.utils import get_solver_literal_lookup, AssumptionSet
from clingexplaid.utils.transformer import AssumptionTransformer
from clingexplaid.utils.muc import CoreComputer
from typing import Set, Tuple, List, Optional

import random
import clingo
import unittest


class TestMain(TestCase):
    """
    Test cases for clingexplaid.
    """

    @staticmethod
    def remove_whitespace(string: str) -> str:
        return string.replace(" ", "").replace("\n", "")

    @staticmethod
    def get_muc_of_program(
            program_string: str,
            assumption_signatures: Set[Tuple[str, int]],
            control: Optional[clingo.Control] = None
    ) -> AssumptionSet:
        ctl = control if control is not None else clingo.Control()

        at = AssumptionTransformer(signatures=assumption_signatures)
        transformed_program = at.parse_string(program_string)

        ctl.add("base", [], transformed_program)
        ctl.ground([("base", [])])

        assumptions = at.get_assumptions(ctl)

        cc = CoreComputer(ctl, assumptions)
        ctl.solve(assumptions=list(assumptions), on_core=cc.shrink)

        return cc.minimal

    def assertMUC(self, muc: Set[Tuple[clingo.Symbol, bool]], valid_mucs_string_lists: List[Set[str]]):
        valid_mucs = [{clingo.parse_term(s) for s in lit_strings} for lit_strings in valid_mucs_string_lists]
        self.assertIn(muc, valid_mucs)

    # TRANSFORMERS

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
            #program base.
            { a(1) }.
            a(2) :- x.
            a(3); a(4) :- x.
            { a((10..15)) }.
            { a(16) }.
            a(17); a(18) :- a(16).
        """
        at = AssumptionTransformer(signatures={('a', 1)})
        result = at.parse_string(program)
        # TODO : This may not neccessary yield the same program since I'm removing whitespace. Maybe there is a better
        #        way of doing this?
        self.assertEqual(self.remove_whitespace(result), self.remove_whitespace(program_transformed))

    def test_assumption_transformer_parse_string_no_signatures(self):
        program = """
            a(1).
            b(2) :- x.
            c(3); c(4) :- x.
            d(10..15).
            e(16).
            f(17); f(18) :- e(16).
        """
        program_transformed = """
            #program base.
            { a(1) }.
            b(2) :- x.
            c(3); c(4) :- x.
            { d((10..15)) }.
            { e(16) }.
            f(17); f(18) :- e(16).
        """
        at = AssumptionTransformer()
        result = at.parse_string(program)
        # TODO : This may not neccessary yield the same program since I'm removing whitespace. Maybe there is a better
        #        way of doing this?
        self.assertEqual(self.remove_whitespace(result), self.remove_whitespace(program_transformed))

    # MUC

    def test_core_computer_shrink_single_muc(self):
        ctl = clingo.Control()

        program = """
        a(1..5).
        :- a(1), a(4), a(5).
        """
        signatures = {("a", 1)}

        muc = self.get_muc_of_program(
            program_string=program,
            assumption_signatures=signatures,
            control=ctl
        )

        literal_lookup = get_solver_literal_lookup(ctl)

        self.assertMUC({literal_lookup[a] for a in muc}, [{"a(1)", "a(4)", "a(5)"}])

    def test_core_computer_shrink_single_atomic_muc(self):
        ctl = clingo.Control()

        program = """
        a(1..5).
        :- a(3).
        """
        signatures = {("a", 1)}

        muc = self.get_muc_of_program(
            program_string=program,
            assumption_signatures=signatures,
            control=ctl
        )

        literal_lookup = get_solver_literal_lookup(ctl)

        self.assertMUC({literal_lookup[a] for a in muc}, [{"a(3)"}])

    def test_core_computer_shrink_multiple_atomic_mucs(self):
        ctl = clingo.Control()

        program = """
        a(1..10).
        :- a(3).
        :- a(5).
        :- a(9).
        """
        signatures = {("a", 1)}

        muc = self.get_muc_of_program(
            program_string=program,
            assumption_signatures=signatures,
            control=ctl
        )

        literal_lookup = get_solver_literal_lookup(ctl)

        self.assertMUC({literal_lookup[a] for a in muc}, [{"a(3)"}, {"a(5)"}, {"a(9)"}])

    def test_core_computer_shrink_multiple_mucs(self):
        ctl = clingo.Control()

        program = """
        a(1..10).
        :- a(3), a(9), a(5).
        :- a(5), a(1), a(2).
        :- a(9), a(2), a(7).
        """
        signatures = {("a", 1)}

        muc = self.get_muc_of_program(
            program_string=program,
            assumption_signatures=signatures,
            control=ctl
        )

        literal_lookup = get_solver_literal_lookup(ctl)

        self.assertMUC({literal_lookup[a] for a in muc}, [
            {"a(3)", "a(9)", "a(5)"},
            {"a(5)", "a(1)", "a(2)"},
            {"a(9)", "a(2)", "a(7)"},
        ])

    def test_core_computer_shrink_large_instance_random(self):
        ctl = clingo.Control()

        n_assumptions = 1000
        random_core = random.choices(range(n_assumptions), k=10)
        program = f"""
        a(1..{n_assumptions}).
        :- {', '.join([f"a({i})" for i in random_core])}.
        """
        signatures = {("a", 1)}

        muc = self.get_muc_of_program(
            program_string=program,
            assumption_signatures=signatures,
            control=ctl
        )

        literal_lookup = get_solver_literal_lookup(ctl)

        self.assertMUC({literal_lookup[a] for a in muc}, [
            {f"a({i})" for i in random_core}
        ])


if __name__ == "__main__":
    unittest.main()
