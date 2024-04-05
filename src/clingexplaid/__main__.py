"""
The main entry point for the application.
"""

import sys

from clingo.application import clingo_main

from .utils.logging import configure_logging, get_logger
from .utils.parser import get_parser
from .utils.cli import ClingoExplaidApp


def main() -> None:
    """
    Run the main function.
    """

    clingo_main(ClingoExplaidApp(sys.argv[0]), sys.argv[1:] + ["-V0"])


if __name__ == "__main__":
    main()
