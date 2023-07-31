import sys

from typing import Union
from pathlib import Path

from clingo.application import Application, clingo_main

from clingexplaid.utils.transformer import AssumptionTransformer
from clingexplaid.utils.muc import CoreComputer
from clingexplaid.utils import get_solver_literal_lookup


def read_file(path: Union[Path, str]) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


class CoreComputerApp(Application):
    program_name: str = "core-computer"
    version: str = "0.1"

    def __init__(self, name):
        self.signatures = {}
        pass

    @staticmethod
    def _parse_option(input_string: str) -> bool:
        print("OPTION", input_string)
        return True

    def _parse_assumption_signature(self, input_string: str) -> bool:
        signature_strings = input_string.strip().split(",")
        signatures = {}
        for sig_string in signature_strings:
            if not sig_string:
                continue
            if "/" in sig_string:
                signature, arity = sig_string.split("/")[:2]
                signatures[signature] = arity
            else:
                signatures[sig_string] = 0
        print("ASSUMPTION SIGNATURE", input_string, signature_strings, signatures)
        self.signatures = signatures
        return True

    def register_options(self, options):
        """
        See clingo.clingo_main().
        """

        group = "MUC Options"

        options.add(
            group,
            "assumption-signatures",
            "All facts matching with this signature will be converted to assumptions for finding a MUC "
            "(default: all facts)",
            self._parse_assumption_signature
        )

    def main(self, ctl, files):
        program_strings = []
        for f in files:
            program_strings.append(read_file(f))
        program_string_full = "\n".join(program_strings)
        program_string_full = """
        hallo(1,2).
        hallo(1,3).
        :- hallo(1,_).
        """

        signature_set = set(self.signatures.items()) if self.signatures else None
        at = AssumptionTransformer(signatures=signature_set)
        program_transformed = at.parse_string(program_string_full)

        ctl.add("base", [], program_transformed)
        ctl.ground([("base", [])])

        literal_lookup = get_solver_literal_lookup(ctl)

        assumptions = at.get_assumptions(ctl)

        cc = CoreComputer(ctl, assumptions)
        ctl.solve(assumptions=list(assumptions), on_core=cc.shrink)

        if cc.minimal is None:
            print("SATISFIABLE: Instance has no MUCs")
            return

        result = " ".join([str(literal_lookup[a]) for a in cc.minimal])

        muc_id = 1
        print(f"MUC: {muc_id}")
        print(result)
