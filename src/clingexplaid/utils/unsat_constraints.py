"""
Unsat Constraint Utilities
"""

import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import List, Optional, Tuple

import clingo

from .transformer import ConstraintTransformer, FactTransformer
from ..utils import get_signatures_from_model_string


UNSAT_CONSTRAINT_SIGNATURE = "__unsat__"


class UnsatConstraintComputer:
    """
    A container class that allows for a passed unsatisfiable program_string to identify the underlying constraints
    making it unsatisfiable
    """

    def __init__(
        self,
        control: Optional[clingo.Control] = None,
    ):
        self.control = control if control is not None else clingo.Control()
        self.program_transformed = None
        self.initialized = False

        self.included_files = set()
        self.file_constraint_lookup = dict()

    def parse_string(self, program_string: str) -> None:
        ct = ConstraintTransformer(UNSAT_CONSTRAINT_SIGNATURE, include_id=True)
        self.program_transformed = ct.parse_string(program_string)
        self.initialized = True

    def parse_files(self, files: List[str]) -> None:
        ct = ConstraintTransformer(UNSAT_CONSTRAINT_SIGNATURE, include_id=True)
        if not files:
            program_transformed = ct.parse_files("-")
        else:
            for file in files:
                # add includes to included_files for every file
                self._register_included_files(file)
            program_transformed = ct.parse_files(files)
        self.program_transformed = program_transformed
        self.initialized = True

    def _register_included_files(self, file: str) -> None:
        absolute_file_path = str(Path(file).absolute().resolve())
        # skip if file was already checked for includes
        if absolute_file_path in self.included_files:
            return
        self.included_files.add(absolute_file_path)

        included_filenames = []
        with open(file, "r") as f:
            result = re.search(r'#include "([^"]*)".', str(f.read()))
            if result is not None:
                included_filenames = list(result.groups())

        for included_file in included_filenames:
            # join original file relative path with included files -> absolute path
            absolute_file_path = str(
                Path(file).parent.joinpath(Path(included_file)).absolute().resolve()
            )
            if absolute_file_path not in self.included_files:
                self.included_files.add(absolute_file_path)
                self._register_included_files(absolute_file_path)

    def _create_file_constraint_lookup(self) -> None:
        for file in self.included_files:
            with open(file, "r") as f:
                rule_strings = [rule.strip() for rule in f.read().split(".")]
                constraints = [rule for rule in rule_strings if rule.startswith(":-")]
                self.file_constraint_lookup[file] = constraints

    def get_constraint_location(self, constraint_string: str) -> Tuple[str, int]:
        self._create_file_constraint_lookup()
        file_similarities = {f: 0.0 for f in self.included_files}
        best_constraints = dict()
        for file, constraints in self.file_constraint_lookup.items():
            for constraint in constraints:
                string_similarity = SequenceMatcher(
                    None, constraint_string, constraint
                ).ratio()
                # update similarity dictionary to find file with the highest matching constraint
                if string_similarity > file_similarities[file]:
                    file_similarities[file] = string_similarity
                    best_constraints[file] = constraint
        # get file with the highest similarity
        best_matching_file = max(file_similarities.items(), key=lambda x: x[1])[0]
        # get the line number from the file
        original_constraint = best_constraints[best_matching_file]
        line_number = -1
        with open(best_matching_file, "r") as f:
            for i, line in enumerate(f.readlines(), 1):
                # this currently only works for non-multiline constraints!
                if original_constraint in line:
                    line_number = i
        return best_matching_file, line_number

    def get_unsat_constraints(
        self, assumption_string: Optional[str] = None
    ) -> List[str]:
        # only execute if the UnsatConstraintComputer was properly initialized
        if not self.initialized:
            raise ValueError(
                "UnsatConstraintComputer is not properly initialized. To do so call either `parse_files` "
                "or `parse_string`."
            )

        program_string = self.program_transformed
        # if an assumption string is provided use a FactTransformer to remove interfering facts
        if assumption_string is not None and len(assumption_string) > 0:
            assumptions_signatures = set(
                get_signatures_from_model_string(assumption_string).items()
            )
            ft = FactTransformer(signatures=assumptions_signatures)
            # first remove all facts from the programs matching the assumption signatures from the assumption_string
            program_string = ft.parse_string(program_string)
            # then add the assumed atoms as the only remaining facts
            program_string += "\n" + ". ".join(assumption_string.split()) + "."

        # add minimization soft constraint to optimize for the smallest set of unsat constraints
        minimizer_rule = f"#minimize {{1,X : {UNSAT_CONSTRAINT_SIGNATURE}(X)}}."
        program_string = program_string + "\n" + minimizer_rule

        # create a rule lookup for every constraint in the program associated with it's unsat id
        constraint_lookup = {}
        for line in program_string.split("\n"):
            id_re = re.compile(f"{UNSAT_CONSTRAINT_SIGNATURE}\(([1-9][0-9]*)\)")
            match_result = id_re.match(line)
            if match_result is None:
                continue
            constraint_id = match_result.group(1)
            constraint_lookup[int(constraint_id)] = (
                str(line)
                .replace(f"{UNSAT_CONSTRAINT_SIGNATURE}({constraint_id})", "")
                .strip()
            )

        self.control.add("base", [], program_string)
        self.control.ground([("base", [])])

        with self.control.solve(yield_=True) as solve_handle:
            model = solve_handle.model()
            unsat_constraint_atoms = []
            while model is not None:
                unsat_constraint_atoms = [
                    a
                    for a in model.symbols(atoms=True)
                    if a.match(UNSAT_CONSTRAINT_SIGNATURE, 1, True)
                ]
                solve_handle.resume()
                model = solve_handle.model()
            unsat_constraints = []
            for a in unsat_constraint_atoms:
                constraint = constraint_lookup.get(a.arguments[0].number)
                unsat_constraints.append(constraint)

            return unsat_constraints


__all__ = [
    UnsatConstraintComputer.__name__,
]
