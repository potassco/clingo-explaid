"""
Command Line Interface Utilities
"""

import configparser
import functools
import sys
from pathlib import Path
from typing import Dict, Callable
from importlib.metadata import version

import clingo
from clingo.application import Application
from clingox.reify import reify_program

from clingexplaid.utils import get_solver_literal_lookup
from clingexplaid.utils.logger import BACKGROUND_COLORS, COLORS
from clingexplaid.utils.muc import CoreComputer
from clingexplaid.utils.transformer import AssumptionTransformer


class CoreComputerApp(Application):
    """
    Application class realizing the CoreComputer functionality of the `clingexplaid.utils.muc.CoreComputer` class.
    """

    program_name: str = "core-computer"
    version: str = "0.1"

    def __init__(self, name):
        # pylint: disable = unused-argument
        self.signatures = {}
        self.method = 1
        self.muc_id = 1

    def _parse_assumption_signature(self, input_string: str) -> bool:
        # signature_strings = input_string.strip().split(",")
        signature_list = input_string.split("/")
        if len(signature_list) != 2:
            print("Not valid format for signature, expected name/arity")
            return False
        self.signatures[signature_list[0]] = int(signature_list[1])
        return True

    def _parse_mode(self, input_string: str) -> bool:
        try:
            method_id = int(input_string.strip())
        except ValueError:
            print("Not valid format for mode, expected 1 or 2")
            return False
        if method_id in (1, 2):
            self.method = method_id
            return True
        return False

    def print_model(self, model, _):
        return

    def register_options(self, options):
        """
        See clingo.clingo_main().
        """

        group = "MUC Options"

        options.add(
            group,
            "assumption-signature,a",
            "Facts matching with this signature will be converted to assumptions for finding a MUC "
            "(default: all facts)",
            self._parse_assumption_signature,
            multi=True,
        )
        options.add(
            group,
            "muc-method,m",
            "This sets the method of finding the MUCs. (1) Iterative Deletion [default] (2) Meta Encoding",
            self._parse_mode,
        )

    def _find_single_muc(self, control: clingo.Control, files):
        signature_set = set(self.signatures.items()) if self.signatures else None
        at = AssumptionTransformer(signatures=signature_set)
        if not files:
            program_transformed = at.parse_files("-")
            print("Reading from -")
        else:
            program_transformed = at.parse_files(files)
            print(f"Reading from {files[0]} {'...' if len(files) > 1 else ''}")

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

        result = " ".join([str(literal_lookup[a]) for a in cc.minimal])

        muc_id = 1
        print(
            f"{BACKGROUND_COLORS['BLUE']} MUC: {muc_id} {COLORS['NORMAL']}{COLORS['DARK_BLUE']}{COLORS['NORMAL']}"
        )
        print(f"{COLORS['BLUE']}{result}{COLORS['NORMAL']}")

    def _find_multi_mucs(self, control: clingo.Control, files):
        print("ASP APPROACH")

        signature_set = set(self.signatures.items()) if self.signatures else None
        at = AssumptionTransformer(signatures=signature_set)
        if not files:
            program_transformed = at.parse_files("-")
            print("Reading from -")
        else:
            program_transformed = at.parse_files(files)
            print(f"Reading from {files[0]} {'...' if len(files) > 1 else ''}")

        # TODO: Ok this is not a nice way to do it but I have no clue how to do it otherwise :)
        arguments = sys.argv[1:]
        constant_names = []
        next_is_const = False
        for arg in arguments:
            if next_is_const:
                constant_name = arg.strip().split("=")[0]
                constant_names.append(constant_name)
                next_is_const = False
            if arg == "-c":
                next_is_const = True

        constants = {name: control.get_const(name) for name in constant_names}

        # First Grounding for getting the assumptions
        assumption_control = clingo.Control([f"-c {k}={str(v)}" for k, v in constants.items()])
        assumption_control.add("base", [], program_transformed)
        assumption_control.ground([("base", [])])

        literal_lookup = get_solver_literal_lookup(assumption_control)

        additional_rules = []

        assumption_signatures = set()
        for assumption_literal in at.get_assumptions(assumption_control, constants=constants):
            assumption = literal_lookup[assumption_literal]
            assumption_signatures.add((assumption.name, len(assumption.arguments)))
            additional_rules.append(f"_assumption({str(assumption)}).")
            additional_rules.append(f"_muc({assumption}) :- {assumption}.")

        for signature, arity in assumption_signatures:
            additional_rules.append(f"#show {signature}/{arity}.")

        final_program = "\n".join((
                # add constants like this because clingox reify doesn't support a custom control or other way to
                # provide constants.
                "\n".join([f"#const {k}={str(v)}."for k, v in constants.items()]),
                program_transformed,
                "#show _muc/1.",
                "\n".join(additional_rules),
        ))

        # Implicit Grounding for reification

        symbols = reify_program(final_program)
        reified_program = "\n".join([f"{str(s)}." for s in symbols])

        with open(Path(__file__).resolve().parent.joinpath("logic_programs/asp_approach.lp"), "r") as f:
            meta_encoding = f.read()

        # Second Grounding to get MUCs with original control

        control.add("base", [], reified_program)
        control.add("base", [], meta_encoding)

        control.configuration.solve.enum_mode = "domRec"
        control.configuration.solver.heuristic = "Domain"

        control.ground([("base", [])])

        control.solve(on_model=self.print_found_muc)

    def print_found_muc(self, model):
        result = ".\n".join([str(a) for a in model.symbols(shown=True)])
        if result:
            result += "."
        print(
            f"{BACKGROUND_COLORS['BLUE']} MUC: {self.muc_id} {COLORS['NORMAL']}{COLORS['DARK_BLUE']}{COLORS['NORMAL']}"
        )
        print(f"{COLORS['BLUE']}{result}{COLORS['NORMAL']}")
        self.muc_id += 1

    def main(self, control, files):
        print("clingexplaid", "version", version("clingexplaid"))

        if self.method == 1:
            self._find_single_muc(control, files)
        elif self.method == 2:
            self._find_multi_mucs(control, files)
