"""
Command Line Interface Utilities
"""

import configparser
import functools
from pathlib import Path
from typing import Dict, Callable

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

        # First Grounding for getting the assumptions
        control.add("base", [], program_transformed)
        control.ground([("base", [])])

        literal_lookup = get_solver_literal_lookup(control)

        additional_rules = []

        assumption_signatures = set()
        for assumption_literal in at.get_assumptions(control):
            assumption = literal_lookup[assumption_literal]
            assumption_signatures.add((assumption.name, len(assumption.arguments)))
            additional_rules.append(f"_assumption({str(assumption)}).")
            additional_rules.append(f"_muc({assumption}) :- {assumption}.")

        for signature, arity in assumption_signatures:
            additional_rules.append(f"#show {signature}/{arity}.")

        final_program = "\n".join((
                program_transformed,
                "#show _muc/1.",
                "\n".join(additional_rules),
        ))

        # print(final_program)

        # Implicit Grounding for reification

        symbols = reify_program(final_program)
        reified_program = "\n".join([f"{str(s)}." for s in symbols])

        # print(reified_program)

        with open(Path(__file__).resolve().parent.joinpath("logic_programs/asp_approach.lp"), "r") as f:
            meta_encoding = f.read()

        # Second Grounding to get MUCs

        muc_control = clingo.Control(["--heuristic=Domain", "--enum-mode=domRec"])
        muc_control.add("base", [], reified_program)
        muc_control.add("base", [], meta_encoding)

        # print(meta_encoding)

        muc_control.ground([("base", [])])

        with muc_control.solve(yield_=True) as solve_handle:
            satisfiable = bool(solve_handle.get().satisfiable)
            model = (
                solve_handle.model().symbols(shown=True, atoms=True)
                if solve_handle.model() is not None
                else []
            )

        print(satisfiable)
        print(".\n".join([str(a) for a in model]))

    def main(self, control, files):
        setup_file_path = Path(__file__).parent.joinpath("../../../setup.cfg")
        setup_config = configparser.ConfigParser()
        setup_config.read(setup_file_path)
        metadata = setup_config["metadata"]
        print(metadata["name"], "version", metadata["version"])

        if self.method == 1:
            self._find_single_muc(control, files)
        elif self.method == 2:
            self._find_multi_mucs(control, files)
