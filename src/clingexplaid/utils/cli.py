import re
from importlib.metadata import version
from typing import Dict, List, Tuple, Optional

import clingo
from clingo.application import Application, Flag

from .muc import CoreComputer
from .transformer import AssumptionTransformer, ConstraintTransformer, FactTransformer
from ..utils import get_solver_literal_lookup, get_signatures_from_model_string
from ..utils.logger import BACKGROUND_COLORS, COLORS


class ClingoExplaidApp(Application):
    """
    Application class for executing clingo-explaid functionality on the command line
    """

    CLINGEXPLAID_METHODS = {
        "muc": "Description for MUC method",
        "unsat-constraints": "Description for unsat-constraints method",
    }

    def __init__(self, name):
        # pylint: disable = unused-argument
        self.methods = set()
        self.method_functions = {
            m: getattr(self, f'_method_{m.replace("-", "_")}')
            for m in self.CLINGEXPLAID_METHODS.keys()
        }
        self.method_flags = {m: Flag() for m in self.CLINGEXPLAID_METHODS.keys()}

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

    def _parse_assumption_signature(self, assumption_signature: str) -> bool:
        if "muc" in self.methods:
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
        assumptions = at.get_assumptions(control)
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
                            output_prefix=f"{COLORS['RED']}├──{COLORS['NORMAL']}",
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
        output_prefix: Optional[str] = None,
    ):
        unsat_constraint_atom = "__unsat__"
        ct = ConstraintTransformer(unsat_constraint_atom, include_id=True)

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

        if assumption_string is not None and len(assumption_string) > 0:
            assumptions_signatures = set(
                get_signatures_from_model_string(assumption_string).items()
            )
            ft = FactTransformer(signatures=assumptions_signatures)
            # first remove all facts from the programs matching the assumption signatures from the assumption_string
            final_program = ft.parse_string(final_program)
            # then add the assumed atoms as the only remaining facts
            final_program += "\n" + ". ".join(assumption_string.split()) + "."

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
            # print(" ".join([str(s) for s in model_symbols_shown]))
            unsat_constraints = []
            for a in unsat_constraint_atoms:
                constraint = constraint_lookup.get(a.arguments[0].number)
                unsat_constraints.append(constraint)

            self._print_unsat_constraints(unsat_constraints, prefix=output_prefix)

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

        # standard case: only one method
        if len(self.methods) == 1:
            method = list(self.methods)[0]
            method_function = self.method_functions[method]
            method_function(control, files)
        # special cases where specific pipelines have to be configured
        elif self.methods == {"muc", "unsat-constraints"}:
            self.method_functions["muc"](control, files, compute_unsat_constraints=True)
