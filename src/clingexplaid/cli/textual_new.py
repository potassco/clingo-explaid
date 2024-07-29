from typing import Dict, List

import clingo
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, Footer, Label, Log, Static, Tab, Tabs

from .textual_style_new import MAIN_CSS


class Header(Static):

    def compose(self) -> ComposeResult:
        yield Label("SAT", id="sat-indicator")
        yield Static()
        yield Button("Select All")
        yield Button("Clear Selection")


class SolverActions(Static):

    def compose(self) -> ComposeResult:
        yield Button("Last")
        yield Button("Next")
        yield Button("All")


class Models(Static):

    def compose(self) -> ComposeResult:
        yield Static("MODEL 1")


class Actions(Static):

    def compose(self) -> ComposeResult:
        yield Static("ACTIONS")


class ClingexplaidTextualApp(App[int]):
    """A textual app for a terminal GUI to use the clingexplaid functionality"""

    CSS = MAIN_CSS

    def __init__(self, files: List[str], constants: Dict[str, str]) -> None:
        super().__init__()

        self.files: List[str] = files
        self.constants: Dict[str, str] = constants

        self._program_satisfiability = self._check_satisfiability()

        self.bind("ctrl+x", "exit", description="Exit", key_display="CTRL+X")

    def compose(self) -> ComposeResult:
        """
        Composes the `ClingexplaidTextualApp`'s components
        """
        ("unsat", "sat")[self._program_satisfiability]
        ("UNSAT", "SAT")[self._program_satisfiability]

        log = Log()
        log.write("DEBUG\n")

        yield Vertical(Header(), SolverActions(), Models(), Actions(), id="content")
        yield log
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
