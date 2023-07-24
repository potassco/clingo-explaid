import sys

from clingo.application import Application, clingo_main


class ClingoApp(Application):
    def __init__(self, name):
        self.program_name = name

    def main(self, ctl, files):
        for f in files:
            ctl.load(f)
        if not files:
            ctl.load("-")
        ctl.ground([("base", [])])
        ctl.solve()


class CoreComputerApp(Application):
    program_name: str = "core-computer"
    version: str = "0.1"

    def __init__(self, name):
        pass

    @staticmethod
    def parse_option(input_string: str):
        print(str)
        return True

    def register_options(self, options):
        """
        See clingo.clingo_main().
        """

        group = "MUC Options"

        options.add(group, "max-mucs", "Defines the maximum number of MUCs returned", self.parse_option)

    def main(self, ctl, files):
        for f in files:
            ctl.load(f)
        if not files:
            ctl.load("-")
        ctl.ground([("base", [])])
        ctl.solve()


clingo_main(CoreComputerApp(sys.argv[0]), sys.argv[1:])
