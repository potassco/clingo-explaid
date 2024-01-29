import re
import sys
from importlib.metadata import version
from typing import Dict, List, Tuple, Optional

import clingo
from clingo.application import Application, Flag

from .logger import BACKGROUND_COLORS, COLORS
from .muc import CoreComputer
from .propagators import DecisionOrderPropagator
from .transformer import AssumptionTransformer, ConstraintTransformer, FactTransformer
from .unsat_constraints import UnsatConstraintComputer
from ..utils import (
    get_solver_literal_lookup,
    get_signatures_from_model_string,
    get_constants_from_arguments,
)


class ClingoExplaidApp(Application):
    """
    Application class for executing clingo-explaid functionality on the command line
    """

    CLINGEXPLAID_METHODS = {
        "muc": "Description for MUC method",
        "unsat-constraints": "Description for unsat-constraints method",
        "show-decisions": "Visualize the decision process of clingo during solving",
    }

    def __init__(self, name):
        # pylint: disable = unused-argument
        self.methods = set()
        self.method_functions = {
            m: getattr(self, f'_method_{m.replace("-", "_")}')
            for m in self.CLINGEXPLAID_METHODS.keys()
        }
        self.method_flags = {m: Flag() for m in self.CLINGEXPLAID_METHODS.keys()}
        self.argument_constants = dict()

        # SHOW DECISIONS
        self._show_decisions_decision_signatures = {}
        self._show_decisions_model_id = 1

        # MUC
        self._muc_assumption_signatures = {}
        self._muc_id = 1

    def _initialize(self) -> None:
        # add enabled methods to self.methods
        for method, flag in self.method_flags.items():
            if flag.flag:
                self.methods.add(method)

        if len(self.methods) == 0:
            raise ValueError(
                f"Clingexplaid was called without any method, pleas select at least one of the following methods: "
                f"[{', '.join(['--' + str(m) for m in self.CLINGEXPLAID_METHODS.keys()])}]"
            )

    @staticmethod
    def _parse_signature(signature_string: str) -> Tuple[str, int]:
        match_result = re.match(r"^([a-zA-Z]+)/([1-9][0-9]*)$", signature_string)
        if match_result is None:
            raise ValueError("Wrong signature Format")
        return match_result.group(1), int(match_result.group(2))

    def _parse_assumption_signature(self, assumption_signature: str) -> bool:
        if not self.method_flags["muc"]:
            print(
                "PARSE ERROR: The assumption signature option is only available if the flag --muc is enabled"
            )
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
        self._muc_assumption_signatures[signature] = arity
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

    def register_options(self, options):
        group = "Clingo-Explaid Methods"

        for method, description in self.CLINGEXPLAID_METHODS.items():
            options.add_flag(
                group=group,
                option=method,
                description=description,
                target=self.method_flags[method],
            )

        group = "MUC Options"

        options.add(
            group,
            "assumption-signature,a",
            "Facts matching with this signature will be converted to assumptions for finding a MUC "
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
        signature_set = (
            set(self._muc_assumption_signatures.items()) if signatures else None
        )
        at = AssumptionTransformer(signatures=signature_set)
        if not files:
            program_transformed = at.parse_files("-")
        else:
            program_transformed = at.parse_files(files)
        return program_transformed, at

    def _print_muc(self, muc) -> None:
        print(
            f"{BACKGROUND_COLORS['BLUE']} MUC {BACKGROUND_COLORS['LIGHT_BLUE']} {self._muc_id} {COLORS['NORMAL']}"
        )
        print(f"{COLORS['BLUE']}{muc}{COLORS['NORMAL']}")
        self._muc_id += 1

    def _method_muc(
        self,
        control: clingo.Control,
        files: List[str],
        compute_unsat_constraints: bool = False,
    ):
        program_transformed, at = self._apply_assumption_transformer(
            signatures=self._muc_assumption_signatures, files=files
        )

        control.add("base", [], program_transformed)
        control.ground([("base", [])])

        literal_lookup = get_solver_literal_lookup(control)
        assumptions = at.get_assumptions(control, constants=self.argument_constants)
        cc = CoreComputer(control, assumptions)

        max_models = int(control.configuration.solve.models)
        print("Solving...")

        # Case: Finding a single MUC
        if max_models == -1:
            control.solve(assumptions=list(assumptions), on_core=cc.shrink)

            if cc.minimal is None:
                print("SATISFIABLE: Instance has no MUCs")
                return

            muc_string = " ".join([str(literal_lookup[a]) for a in cc.minimal])
            self._print_muc(muc_string)

        # Case: Finding multiple MUCs
        if max_models >= 0:
            program_unsat = False
            with control.solve(
                assumptions=list(assumptions), yield_=True
            ) as solve_handle:
                if not solve_handle.get().satisfiable:
                    program_unsat = True

            if program_unsat:
                for muc in cc.get_multiple_minimal(max_mucs=max_models):
                    muc_string = " ".join([str(literal_lookup[a]) for a in muc])
                    self._print_muc(muc_string)

                    if compute_unsat_constraints:
                        self._method_unsat_constraints(
                            control=clingo.Control(),
                            files=files,
                            assumption_string=muc_string,
                            output_prefix_active=f"{COLORS['RED']}├──{COLORS['NORMAL']}",
                            output_prefix_passive=f"{COLORS['RED']}│  {COLORS['NORMAL']}",
                        )

    def _print_unsat_constraints(
        self, unsat_constraints, prefix: Optional[str] = None
    ) -> None:
        if prefix is None:
            prefix = ""
        print(
            f"{prefix}{BACKGROUND_COLORS['RED']} Unsat Constraints {COLORS['NORMAL']}"
        )
        for c in unsat_constraints:
            print(f"{prefix}{COLORS['RED']}{c}{COLORS['NORMAL']}")

    def _method_unsat_constraints(
        self,
        control: clingo.Control,
        files: List[str],
        assumption_string: Optional[str] = None,
        output_prefix_active: str = "",
        output_prefix_passive: str = "",
    ):
        # register DecisionOrderPropagator if flag is enabled
        if self.method_flags["show-decisions"]:
            decision_signatures = set(self._show_decisions_decision_signatures.items())
            dop = DecisionOrderPropagator(
                signatures=decision_signatures, prefix=output_prefix_passive
            )
            control.register_propagator(dop)

        ucc = UnsatConstraintComputer(control=control)
        ucc.parse_files(files)
        unsat_constraints = ucc.get_unsat_constraints(
            assumption_string=assumption_string
        )
        self._print_unsat_constraints(unsat_constraints, prefix=output_prefix_active)

    def _print_model(
        self,
        model,
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
    ):
        decision_signatures = set(self._show_decisions_decision_signatures.items())
        dop = DecisionOrderPropagator(signatures=decision_signatures)
        control.register_propagator(dop)
        for f in files:
            control.load(f)
        if not files:
            control.load("-")
        control.ground()
        control.solve(on_model=lambda model: self._print_model(model, "├", "│"))

    def print_model(self, model, _):
        return

    def main(self, control, files):
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
        elif self.methods == {"muc", "unsat-constraints"}:
            self.method_functions["muc"](control, files, compute_unsat_constraints=True)
        elif self.methods == {"muc", "unsat-constraints", "show-decisions"}:
            self.method_functions["muc"](control, files, compute_unsat_constraints=True)
        elif self.methods == {"unsat-constraints", "show-decisions"}:
            self.method_functions["unsat-constraints"](control, files)
        else:
            print(
                f"METHOD ERROR: the combination of the methods {[f'--{m}' for m in self.methods]} is invalid. "
                f"Please remove the conflicting method flags"
            )
