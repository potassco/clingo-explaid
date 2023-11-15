import re
from importlib.metadata import version
from typing import Dict, List, Tuple

import clingo
from clingo.application import Application

from .muc import CoreComputer
from .transformer import AssumptionTransformer, ConstraintTransformer
from ..utils import get_solver_literal_lookup
from ..utils.logger import BACKGROUND_COLORS, COLORS


class ClingoExplaidApp(Application):
    """
    Application class for executing clingo-explaid functionality on the command line
    """

    CLINGEXPLAID_METHODS = {"muc", "unsat-constraints"}

    def __init__(self, name):
        # pylint: disable = unused-argument
        self.method = None
        self.method_functions = {
            m: getattr(self, f'_method_{m.replace("-", "_")}')
            for m in self.CLINGEXPLAID_METHODS
        }

        # MUC
        self._muc_assumption_signatures = {}
        self._muc_id = 1

    def _check_integrity(self) -> None:
        if self.method is None:
            raise ValueError(
                "No method assigned: A valid clingexplaid method has to be provided with --method,-m"
            )

    def _parse_method(self, method: str) -> bool:
        method_string = method.replace("=", "").strip()
        if method_string not in self.CLINGEXPLAID_METHODS:
            method_strings = ", ".join(
                [f"[{str(k)}]" for k in self.CLINGEXPLAID_METHODS]
            )
            print(
                "PARSE ERROR: The clingexplaid method has to be one of the following:",
                method_strings,
            )
            return False
        self.method = method_string
        return True

    def _parse_assumption_signature(self, assumption_signature: str) -> bool:
        if self.method != "muc":
            print(
                "PARSE ERROR: The assumption signature option is only available for --mode=muc"
            )
            return False
        assumption_signature_string = assumption_signature.replace("=", "").strip()
        match_result = re.match(
            r"^([a-zA-Z]+)/([1-9][0-9]*)$", assumption_signature_string
        )
        if match_result is None:
            print(
                "PARSE ERROR: Wrong signature format. The assumption signatures have to follow the format "
                "<assumption-name>/<arity>"
            )
            return False
        self._muc_assumption_signatures[match_result.group(1)] = int(
            match_result.group(2)
        )
        return True

    def register_options(self, options):
        group = "Clingo-Explaid Options"

        method_string_list = "\n".join([f"\t- {k}" for k in self.CLINGEXPLAID_METHODS])
        options.add(
            group,
            "method,m",
            "For selecting the mode of clingexplaid. Possible options for <arg> are:\n"
            + method_string_list,
            self._parse_method,
            multi=False,
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

    def _method_muc(self, control: clingo.Control, files: List[str]):
        print("method: muc")

        program_transformed, at = self._apply_assumption_transformer(
            signatures=self._muc_assumption_signatures, files=files
        )

        control.add("base", [], program_transformed)
        control.ground([("base", [])])

        literal_lookup = get_solver_literal_lookup(control)
        assumptions = at.get_assumptions(control)
        cc = CoreComputer(control, assumptions)

        print("Solving...")
        control.solve(assumptions=list(assumptions), on_core=cc.shrink)

        if cc.minimal is None:
            print("SATISFIABLE: Instance has no MUCs")
            return

        muc_string = " ".join([str(literal_lookup[a]) for a in cc.minimal])
        self._print_muc(muc_string)

    def _print_unsat_constraints(self, unsat_constraints) -> None:
        print(f"{BACKGROUND_COLORS['RED']} Unsat Constraints {COLORS['NORMAL']}")
        for c in unsat_constraints:
            print(f"{COLORS['RED']}{c}{COLORS['NORMAL']}")

    def _method_unsat_constraints(self, control: clingo.Control, files: List[str]):
        print("method: unsat-constraints")

        unsat_constraint_atom = "__unsat__"
        ct = ConstraintTransformer(unsat_constraint_atom, include_id=True)

        print(files)

        if not files:
            program_transformed = ct.parse_files("-")
        else:
            program_transformed = ct.parse_files(files)

        minimizer_rule = f"#minimize {{1,X : {unsat_constraint_atom}(X)}}."
        final_program = program_transformed + "\n" + minimizer_rule

        constraint_lookup = {}
        for line in final_program.split("\n"):
            id_re = re.compile(f"{unsat_constraint_atom}\(([1-9][0-9]*)\)")
            match_result = id_re.match(line)
            if match_result is None:
                continue
            constraint_id = match_result.group(1)
            constraint_lookup[int(constraint_id)] = (
                str(line)
                .replace(f"{unsat_constraint_atom}({constraint_id})", "")
                .strip()
            )

        control.add("base", [], final_program)
        control.ground([("base", [])])

        with control.solve(yield_=True) as solve_handle:
            model = solve_handle.model()
            unsat_constraint_atoms = []
            model_symbols_shown = []
            while model is not None:
                unsat_constraint_atoms = [
                    a
                    for a in model.symbols(atoms=True)
                    if a.match(unsat_constraint_atom, 1, True)
                ]
                model_symbols_shown = model.symbols(shown=True)
                solve_handle.resume()
                model = solve_handle.model()
            print(" ".join([str(s) for s in model_symbols_shown]))
            unsat_constraints = []
            for a in unsat_constraint_atoms:
                constraint = constraint_lookup.get(a.arguments[0].number)
                unsat_constraints.append(constraint)

            self._print_unsat_constraints(unsat_constraints)

    def print_model(self, model, _):
        return

    def main(self, control, files):
        print("clingexplaid", "version", version("clingexplaid"))
        self._check_integrity()

        # printing the input files
        if not files:
            print("Reading from -")
        else:
            print(f"Reading from {files[0]} {'...' if len(files) > 1 else ''}")

        method_function = self.method_functions[self.method]
        method_function(control, files)
