"""
The main entry point for the application.
"""
import sys

from clingo.application import clingo_main

from clingexplaid.utils.cli import CoreComputerApp


def main():
    """
    Main function calling the application class
    """
    clingo_main(CoreComputerApp(sys.argv[0]), sys.argv[1:]+["-V0"])
    sys.exit()


if __name__ == "__main__":
    main()
