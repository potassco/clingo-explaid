"""
The main entry point for the application.
"""

import sys

from clingo.application import clingo_main

from .cli.clingo_app import ClingoExplaidApp
from .cli.textual_gui import ClingexplaidTextualApp

RUN_TEXTUAL_GUI = False


def main() -> None:
    """
    Run the main function.
    """

    if RUN_TEXTUAL_GUI:
        app = ClingexplaidTextualApp()
        app.run()
    else:
        clingo_main(ClingoExplaidApp(sys.argv[0]), sys.argv[1:] + ["-V0"])


if __name__ == "__main__":
    main()
