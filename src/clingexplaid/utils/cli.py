import re
from importlib.metadata import version

from clingo.application import Application


class ClingoExplaidApp(Application):
    """
    Application class for executing clingo-explaid functionality on the command line
    """

    CLINGEXPLAID_METHODS = {
        "muc": None,
        "unsat_constraints": None
    }

    def __init__(self, name):
        # pylint: disable = unused-argument
        self.method = None

        # MUC
        self._muc_assumption_signatures = {}
        self._muc_id = 1

    def _check_integrity(self) -> None:
        if self.method is None:
            raise ValueError("No method assigned: A valid clingexplaid method has to be provided with --method,-m")

    def _parse_method(self, method: str) -> bool:
        method_string = method.replace("=", "").strip()
        if method_string not in self.CLINGEXPLAID_METHODS:
            method_strings = ", ".join([f"[{str(k)}]" for k in self.CLINGEXPLAID_METHODS.keys()])
            print("PARSE ERROR: The clingexplaid method has to be one of the following:", method_strings)
            return False
        self.method = method_string
        return True

    def _parse_assumption_signature(self, assumption_signature: str) -> bool:
        if self.method != "muc":
            print("PARSE ERROR: The assumption signature option is only available for --mode=muc")
            return False
        assumption_signature_string = assumption_signature.replace("=", "").strip()
        match_result = re.match(r"^([a-zA-Z]+)/([1-9][0-9]*)$", assumption_signature_string)
        if match_result is None:
            print("PARSE ERROR: Wrong signature format. The assumption signatures have to follow the format "
                  "<assumption-name>/<arity>")
            return False
        self._muc_assumption_signatures[match_result.group(1)] = int(match_result.group(2))
        return True

    def register_options(self, options):
        group = "Clingo-Explaid Options"

        method_string_list = "\n".join([f"\t- {k}" for k in self.CLINGEXPLAID_METHODS.keys()])
        options.add(
            group,
            "method,m",
            "For selecting the mode of clingexplaid. Possible options for <arg> are:\n" + method_string_list,
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

    def print_model(self, model, _):
        return

    def main(self, control, files):
        print("clingexplaid", "version", version("clingexplaid"))
        self._check_integrity()
