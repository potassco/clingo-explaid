"""
Command Line Interface Utilities
"""

from clingo.application import Application

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

    def _parse_assumption_signature(self, input_string: str) -> bool:
        # signature_strings = input_string.strip().split(",")
        signature_list = input_string.split("/")
        if len(signature_list) != 2:
            print("Not valid format for signature, expected name/arity")
            return False
        self.signatures[signature_list[0]] = int(signature_list[1])
        return True

    def print_model(self, model, _):
        return

    def register_options(self, options):
        """
        See clingo.clingo_main().
        """

        group = "MUC Options"

        options.add(
            group,
            "assumption-signatures,a",
            "All facts matching with this signature will be converted to assumptions for finding a MUC "
            "(default: all facts)",
            self._parse_assumption_signature,
            multi=True,
        )

    def main(self, control, files):
        signature_set = set(self.signatures.items()) if self.signatures else None
        at = AssumptionTransformer(signatures=signature_set)
        if not files:
            program_transformed = at.parse_files("-")
        else:
            program_transformed = at.parse_files(files)

        control.add("base", [], program_transformed)
        control.ground([("base", [])])

        literal_lookup = get_solver_literal_lookup(control)

        assumptions = at.get_assumptions(control)

        cc = CoreComputer(control, assumptions)
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
