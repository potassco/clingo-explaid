"""
App Module: clingexplaid CLI clingo app
"""

import re
import sys
from importlib.metadata import version
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Set, Tuple
from warnings import warn

import clingo
from clingo.application import Application, Flag

from ..mus import CoreComputer
from ..transformers import AssumptionTransformer, OptimizationRemover
from ..unsat_constraints import UnsatConstraintComputer
from ..utils import get_constants_from_arguments
from ..utils.logging import BACKGROUND_COLORS, COLORS
from .textual_gui import ClingexplaidTextualApp

HYPERLINK_MASK = "\033]8;{};{}\033\\{}\033]8;;\033\\"


class ClingoExplaidApp(Application):
    """
    Application class for executing clingo-explaid functionality on the command line
    """

    # pylint: disable = too-many-instance-attributes

    CLINGEXPLAID_METHODS = {
        "mus": "Description for MUS method",
        "unsat-constraints": "Description for unsat-constraints method",
        "show-decisions": "Visualize the decision process of clingo during solving",
    }

    def __init__(self, name: str) -> None:
        # pylint: disable = unused-argument
        self.methods: Set[str] = set()
        self.method_functions: Dict[str, Callable] = {  # type: ignore
            m: getattr(self, f'_method_{m.replace("-", "_")}') for m in self.CLINGEXPLAID_METHODS
        }
        self.method_flags: Dict[str, Flag] = {m: Flag() for m in self.CLINGEXPLAID_METHODS}
        self.argument_constants: Dict[str, str] = {}

        # SHOW DECISIONS
        self._show_decisions_decision_signatures: Dict[str, int] = {}
        self._show_decisions_model_id: int = 1

        # MUS
        self._mus_assumption_signatures: Dict[str, int] = {}
        self._mus_id: int = 1

    def _initialize(self) -> None:
        # add enabled methods to self.methods
        for method, flag in self.method_flags.items():
            if flag.flag:
                self.methods.add(method)

        if len(self.methods) == 0:
            raise ValueError(
                f"Clingexplaid was called without any method, please select at least one of the following methods: "
                f"[{', '.join(['--' + str(m) for m in self.CLINGEXPLAID_METHODS])}]"
            )

    @staticmethod
    def _parse_signature(signature_string: str) -> Tuple[str, int]:
        match_result = re.match(r"^([a-zA-Z]+)/([0-9]+)$", signature_string)
        if match_result is None:
            raise ValueError("Wrong signature Format")
        return match_result.group(1), int(match_result.group(2))

    def _parse_assumption_signature(self, assumption_signature: str) -> bool:
        if not self.method_flags["mus"]:
            print("PARSE ERROR: The assumption signature option is only available if the flag --mus is enabled")
            return False
        assumption_signature_string = assumption_signature.replace("=", "").strip()
        try:
            signature, arity = self._parse_signature(assumption_signature_string)
        except ValueError:
            print(
                "PARSE ERROR: Wrong signature format. The assumption signatures have to follow the format "
                "<assumption-name>/<arity>"
            )
            return False
        self._mus_assumption_signatures[signature] = arity
        return True

    def _parse_decision_signature(self, decision_signature: str) -> bool:
        if not self.method_flags["show-decisions"]:
            print(
                "PARSE ERROR: The decision signature option is only available if the flag --show-decisions is enabled"
            )
            return False
        decision_signature_string = decision_signature.replace("=", "").strip()
        try:
            signature, arity = self._parse_signature(decision_signature_string)
        except ValueError:
            print(
                "PARSE ERROR: Wrong signature format. The decision signatures have to follow the format "
                "<assumption-name>/<arity>"
            )
            return False
        self._show_decisions_decision_signatures[signature] = arity
        return True

    def register_options(self, options: clingo.ApplicationOptions) -> None:
        group = "Clingo-Explaid Methods"

        for method, description in self.CLINGEXPLAID_METHODS.items():
            options.add_flag(
                group=group,
                option=method,
                description=description,
                target=self.method_flags[method],
            )

        group = "MUS Options"

        options.add(
            group,
            "assumption-signature,a",
            "Facts matching with this signature will be converted to assumptions for finding a MUS "
            "(default: all facts)",
            self._parse_assumption_signature,
            multi=True,
        )

        group = "Show Decisions Options"

        options.add(
            group,
            "decision-signature",
            "When --show-decisions is enabled, show only decisions matching with this signature "
            "(default: show all decisions)",
            self._parse_decision_signature,
            multi=True,
        )

        # group = "General Options"

    def _apply_assumption_transformer(
        self, signatures: Dict[str, int], files: List[str]
    ) -> Tuple[str, AssumptionTransformer]:
        signature_set = set(self._mus_assumption_signatures.items()) if signatures else None
        at = AssumptionTransformer(signatures=signature_set)
        if not files:
            program_transformed = at.parse_files("-")
        else:
            program_transformed = at.parse_files(files)
        return program_transformed, at

    def _print_mus(self, mus_string: str) -> None:
        print(f"{BACKGROUND_COLORS['BLUE']} MUS {BACKGROUND_COLORS['LIGHT_BLUE']} {self._mus_id} {COLORS['NORMAL']}")
        print(f"{COLORS['BLUE']}{mus_string}{COLORS['NORMAL']}")
        self._mus_id += 1

    def _method_mus(
        self,
        control: clingo.Control,
        files: List[str],
        compute_unsat_constraints: bool = False,
    ) -> None:
        program_transformed, at = self._apply_assumption_transformer(
            signatures=self._mus_assumption_signatures, files=files
        )

        # remove optimization statements
        optr = OptimizationRemover()
        program_transformed = optr.parse_string(program_transformed)

        control.add("base", [], program_transformed)
        control.ground([("base", [])])

        assumptions = at.get_assumptions(control, constants=self.argument_constants)
        cc = CoreComputer(control, assumptions)

        max_models = int(control.configuration.solve.models)  # type: ignore
        print("Solving...")

        # Case: Finding a single MUS
        if max_models == -1:
            control.solve(assumptions=list(assumptions), on_core=cc.shrink)

            if cc.minimal is None:
                print("SATISFIABLE: Instance has no MUS")
                return
            if len(list(cc.minimal)) == 0:
                print(
                    "NO MUS CONTAINED: The unsatisfiability of this program is not induced by the provided assumptions"
                )
                return

            mus_string = " ".join(cc.mus_to_string(cc.minimal))
            self._print_mus(mus_string)

            if compute_unsat_constraints:
                self._method_unsat_constraints(
                    control=clingo.Control(),
                    files=files,
                    assumption_string=mus_string,
                    output_prefix_active=f"{COLORS['RED']}├──{COLORS['NORMAL']}",
                )

        # Case: Finding multiple MUS
        if max_models >= 0:
            program_unsat = False
            with control.solve(assumptions=list(assumptions), yield_=True) as solve_handle:
                if not solve_handle.get().satisfiable:
                    program_unsat = True

            if program_unsat:
                n_mus = 0
                for mus in cc.get_multiple_minimal(max_mus=max_models):
                    n_mus += 1
                    mus_string = " ".join(cc.mus_to_string(mus))
                    self._print_mus(mus_string)

                    if compute_unsat_constraints:
                        self._method_unsat_constraints(
                            control=clingo.Control(),
                            files=files,
                            assumption_string=mus_string,
                            output_prefix_active=f"{COLORS['RED']}├──{COLORS['NORMAL']}",
                        )
                if not n_mus:
                    print(
                        "NO MUS CONTAINED: The unsatisfiability of this program is not induced by the provided "
                        "assumptions"
                    )
                    return

    def _print_unsat_constraints(
        self,
        unsat_constraints: Dict[int, str],
        ucc: UnsatConstraintComputer,
        prefix: Optional[str] = None,
    ) -> None:
        if prefix is None:
            prefix = ""
        print(f"{prefix}{BACKGROUND_COLORS['RED']} Unsat Constraints {COLORS['NORMAL']}")
        for cid, constraint in unsat_constraints.items():
            location = ucc.get_constraint_location(cid)
            if location is None:
                warn(f"Couldn't find a corresponding file for constraint with id {cid}")
                continue
            relative_file_path = location.begin.filename
            absolute_file_path = str(Path(relative_file_path).absolute().resolve())
            line_beginning = location.begin.line
            line_end = location.end.line
            line_string = (
                f"Line {line_beginning}" if line_beginning == line_end else f"Lines {line_beginning}-{line_end}"
            )
            file_link = "file://" + absolute_file_path
            if " " in absolute_file_path:
                # If there's a space in the filename use a hyperlink
                file_link = HYPERLINK_MASK.format("", file_link, file_link)

            if location is not None:
                print(
                    f"{prefix}{COLORS['RED']}{constraint}"
                    f"{COLORS['GREY']} [ {file_link} ]({line_string}){COLORS['NORMAL']}"
                )
            else:
                print(f"{prefix}{COLORS['RED']}{constraint}{COLORS['NORMAL']}")

    def _method_unsat_constraints(
        self,
        control: clingo.Control,
        files: List[str],
        assumption_string: Optional[str] = None,
        output_prefix_active: str = "",
    ) -> None:
        ucc = UnsatConstraintComputer(control=control)
        ucc.parse_files(files)
        unsat_constraints = ucc.get_unsat_constraints(assumption_string=assumption_string)
        self._print_unsat_constraints(unsat_constraints, ucc=ucc, prefix=output_prefix_active)

    def _print_model(
        self,
        model: clingo.Model,
        prefix_active: str = "",
        prefix_passive: str = "",
    ) -> None:
        print(prefix_passive)
        print(
            f"{prefix_active}"
            f"{BACKGROUND_COLORS['LIGHT-GREY']}{COLORS['BLACK']} Model {COLORS['NORMAL']}{BACKGROUND_COLORS['GREY']} "
            f"{self._show_decisions_model_id} {COLORS['NORMAL']} "
            f"{model}"
        )
        # print(f"{COLORS['BLUE']}{model}{COLORS['NORMAL']}")
        print(prefix_passive)
        self._show_decisions_model_id += 1

    def _method_show_decisions(
        self,
        control: clingo.Control,
        files: List[str],
    ) -> None:
        print(control)  # only for pylint

        app = ClingexplaidTextualApp(files=files, constants={})
        app.run()

    def print_model(self, model: clingo.Model, _) -> None:  # type: ignore
        return

    def main(self, control: clingo.Control, files: Sequence[str]) -> None:
        print("clingexplaid", "version", version("clingexplaid"))
        self._initialize()

        # printing the input files
        if not files:
            print("Reading from -")
        else:
            print(f"Reading from {files[0]} {'...' if len(files) > 1 else ''}")

        self.argument_constants = get_constants_from_arguments(sys.argv)

        # standard case: only one method
        if len(self.methods) == 1:
            method = list(self.methods)[0]
            method_function = self.method_functions[method]
            method_function(control, files)
        # special cases where specific pipelines have to be configured
        elif self.methods == {"mus", "unsat-constraints"}:
            self.method_functions["mus"](control, files, compute_unsat_constraints=True)
        else:
            print(
                f"METHOD ERROR: the combination of the methods {[f'--{m}' for m in self.methods]} is invalid. "
                f"Please remove the conflicting method flags"
            )
