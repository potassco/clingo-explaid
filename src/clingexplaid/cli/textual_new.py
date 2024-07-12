from typing import Dict, Iterable, List, Optional, Type

import clingo
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Footer, Label, Log, Tab, Tabs

from .textual_modes import AbstractMode, MinimalUnsatisfiableSubsetMode, SolvingMode, UnsatisfiableConstraintsMode
from .textual_style_new import MAIN_CSS


class Content(Widget):
    """Generates a greeting."""

    mode = reactive(None, recompose=True)

    def __init__(self, modes: Dict[str, Type[AbstractMode]], id: Optional[str] = None) -> None:
        super().__init__(id=id)
        self.modes: Dict[str, Type[AbstractMode]] = modes

    def compose(self) -> ComposeResult:
        if self.mode is None:
            yield Label(f"No mode currently loaded")
        else:
            yield self.modes[str(self.mode)]()


class ClingexplaidTextualApp(App[int]):
    """A textual app for a terminal GUI to use the clingexplaid functionality"""

    CSS = MAIN_CSS
    MODES_SAT = {mode.mode_id: mode for mode in {SolvingMode}}
    MODES_UNSAT = {mode.mode_id: mode for mode in {MinimalUnsatisfiableSubsetMode, UnsatisfiableConstraintsMode}}

    def __init__(self, files: List[str], constants: Dict[str, str]) -> None:
        super().__init__()

        self.files: List[str] = files
        self.constants: Dict[str, str] = constants

        self._program_satisfiability = self._check_satisfiability()
        self._mode = self._get_mode(initial=True)

        self.bind("ctrl+x", "exit", description="Exit", key_display="CTRL+X")

    def compose(self) -> ComposeResult:
        """
        Composes the `ClingexplaidTextualApp`'s components
        """
        satisfiability_class = ("unsat", "sat")[self._program_satisfiability]
        satisfiability_string = ("UNSAT", "SAT")[self._program_satisfiability]
        yield Horizontal(
            Tabs(*self._compose_tabs()),
            Label(satisfiability_string, id="sat-indicator", classes=satisfiability_class),
            id="header",
        )
        # yield Vertical(*self._get_mode().compose(), id="content")
        yield Content(self._get_mode_dict(), id="content")
        log = Log()
        log.write("DEBUG\n")
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

    @on(Tabs.TabActivated)
    def _tab_switched(self, event: Tabs.TabActivated):
        tab_id = event.tab.id
        self._set_mode(tab_id)
        self.query_one(Log).write(f"switched tab -> {tab_id}\n")

    def _compose_tabs(self) -> Iterable[Tab]:
        for mode in self._get_mode_set():
            tab = Tab(mode.mode_name, id=mode.mode_id)
            yield tab

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

    def _get_mode_dict(self) -> Dict[str, Type[AbstractMode]]:
        return self.MODES_SAT if self._program_satisfiability else self.MODES_UNSAT

    def _get_mode_set(self) -> Iterable[AbstractMode]:
        return sorted(self._get_mode_dict().values(), key=lambda x: x.order)

    def _get_mode(self, initial: bool = False) -> AbstractMode:
        if initial:
            return list(self._get_mode_set())[0]
        else:
            return self._mode

    def _set_mode(self, mode_id: str) -> None:
        mode_dict = self._get_mode_dict()
        if mode_id not in mode_dict:
            raise KeyError("The provided mode ID is not in the registered modes")
        self._mode = mode_dict[mode_id]
        self.query_one(Content).mode = mode_id
