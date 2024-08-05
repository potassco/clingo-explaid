from typing import Dict, List, Optional

import clingo
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, Checkbox, Collapsible, Footer, Label, Log, Select, Static, Tab, Tabs, TextArea

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


class Model(Static):

    def __init__(self, model_id, weight: Optional[int] = None, optimal: bool = False, selected: bool = False):
        super().__init__()
        self._model_id = model_id
        self._weight = weight
        self._optimal = optimal
        self.collapsed: bool = False
        self.selected: bool = selected

        if self._optimal:
            self.add_class("optimal")
        if self.selected:
            self.add_class("selected")

    def compose(self) -> ComposeResult:
        yield Collapsible(
            Collapsible(title="Shown Atoms", classes="result"),
            title=f"Model {self._model_id}",
            collapsed=self.collapsed,
        )
        yield ModelHeader(self, weight=self._weight, optimal=self._optimal)

    def set_selected(self, selected: bool):
        self.selected = selected
        if selected:
            self.add_class("selected")
        else:
            self.remove_class("selected")

    def toggle_selected(self):
        self.set_selected(not self.selected)


class ModelHeader(Static):

    def __init__(self, model: Model, weight: Optional[int] = None, optimal: bool = False):
        super().__init__()
        self._model = model
        self._weight = weight
        self._optimal = optimal

    def compose(self) -> ComposeResult:
        weight_label = Label(str(self._weight), classes="model-cost")
        if self._weight is None:
            weight_label.add_class("hidden")
        yield weight_label
        optimal_label = Label(f"⭐", classes="optimality-indicator hidden")
        if self._optimal:
            optimal_label.remove_class("hidden")
        yield optimal_label
        yield Checkbox(classes="model-selector")
        yield Static()

    @on(Checkbox.Changed)
    def checkbox_changed(self, event: Checkbox.Changed) -> None:
        if event.checkbox == self.query_one(Checkbox):
            self._model.toggle_selected()


class Models(Static):

    def compose(self) -> ComposeResult:
        yield VerticalScroll(
            Model(1, weight=230),
            Model(2, weight=180),
            Model(3, weight=120, optimal=True),
            Model(4, weight=120, optimal=True),
        )


class Filters(Static):

    def compose(self) -> ComposeResult:
        yield Checkbox("All Atoms")
        yield Checkbox("Shown Atoms", value=True)
        yield Checkbox("Theory Atoms")


class Actions(Static):

    def compose(self) -> ComposeResult:
        text_area = TextArea()
        text_area.border_title = "Atoms"
        yield VerticalScroll(
            Select([("Filter", 1)], allow_blank=False),
            Filters(),
            Vertical(text_area, id="inputs"),
        )
        yield Button("Apply", id="apply")
        yield Button("Clear History", id="clear-history")


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
