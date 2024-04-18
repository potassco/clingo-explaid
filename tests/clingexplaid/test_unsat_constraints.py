"""
Tests for the unsat_constraints package
"""

from typing import Dict, Optional
from unittest import TestCase

from clingexplaid.unsat_constraints import UnsatConstraintComputer

from .test_main import TEST_DIR


class TestUnsatConstraints(TestCase):
    """
    Test cases for unsat constraints functionality.
    """

    # UNSAT CONSTRAINT COMPUTER

    def unsat_constraint_computer_helper(
        self,
        constraint_strings: Dict[int, str],
        constraint_lines: Dict[int, int],
        constraint_files: Dict[int, str],
        assumption_string: Optional[str] = None,
    ) -> None:
        """
        Helper function for testing the UnsatConstraintComputer
        """
        for method in ["from_files", "from_string"]:
            program_path = TEST_DIR.joinpath("res/test_program_unsat_constraints.lp")
            ucc = UnsatConstraintComputer()
            if method == "from_files":
                ucc.parse_files([str(program_path)])
            elif method == "from_string":
                with open(program_path, "r", encoding="utf-8") as f:
                    ucc.parse_string(f.read())
            unsat_constraints = ucc.get_unsat_constraints(assumption_string=assumption_string)
            self.assertEqual(set(unsat_constraints.values()), set(constraint_strings.values()))

            for c_id in unsat_constraints:
                loc = ucc.get_constraint_location(c_id)
                if method == "from_files":
                    # only check the source file if .from_files is used to initialize
                    self.assertEqual(loc.begin.filename, constraint_files[c_id])  # type: ignore
                self.assertEqual(loc.begin.line, constraint_lines[c_id])  # type: ignore

    def test_unsat_constraint_computer(self) -> None:
        """
        Testing the UnsatConstraintComputer without assumptions.
        """
        self.unsat_constraint_computer_helper(
            constraint_strings={2: ":- not a."},
            constraint_lines={2: 4},
            constraint_files={2: str(TEST_DIR.joinpath("res/test_program_unsat_constraints.lp"))},
        )

    def test_unsat_constraint_computer_with_assumptions(self) -> None:
        """
        Testing the UnsatConstraintComputer with assumptions.
        """
        self.unsat_constraint_computer_helper(
            constraint_strings={1: ":- a."},
            constraint_lines={1: 3},
            constraint_files={1: str(TEST_DIR.joinpath("res/test_program_unsat_constraints.lp"))},
            assumption_string="a",
        )

    def test_unsat_constraint_computer_not_initialized(self) -> None:
        """
        Testing the UnsatConstraintComputer without initializing it.
        """
        ucc = UnsatConstraintComputer()
        self.assertRaises(ValueError, ucc.get_unsat_constraints)
