from typing import Dict, List

import clingo
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Label, Tab, Tabs

from .textual_modes import SolvingMode
from .textual_style_new import MAIN_CSS


class ClingexplaidTextualApp(App[int]):
    """A textual app for a terminal GUI to use the clingexplaid functionality"""

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=duplicate-code

    CSS = MAIN_CSS

    def __init__(self, files: List[str], constants: Dict[str, str]) -> None:
        super().__init__()

        self.files: List[str] = files
        self.constants: Dict[str, str] = constants

        self.program_satisfiability = self._check_satisfiability()

        self.bind("ctrl+x", "exit", description="Exit", key_display="CTRL+X")

    def compose(self) -> ComposeResult:
        """
        Composes the `ClingexplaidTextualApp`'s components
        """
        satisfiability_class = ("unsat", "sat")[self.program_satisfiability]
        satisfiability_string = ("UNSAT", "SAT")[self.program_satisfiability]
        yield Horizontal(
            Tabs(
                Tab("Solving", id="solving"),
                Tab("Solver Decisions", id="decisions"),
                Tab("Explanation", id="explanation"),
            ),
            Label(satisfiability_string, id="sat-indicator", classes=satisfiability_class),
            id="header",
        )
        yield Vertical(SolvingMode(), id="content")
        yield Footer()

    def action_exit(self) -> None:
        """
        Action to exit the textual application
        """
        self.exit(0)

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        """
        Check if any action may run
        """
        return True

    def _check_satisfiability(self) -> bool:
        control = clingo.Control()
        for file in self.files:
            control.load(file)
        control.ground([("base", [])])
        with control.solve(yield_=True) as solve_handle:
            result = solve_handle.get()
            if result.satisfiable:
                return True
        return False
