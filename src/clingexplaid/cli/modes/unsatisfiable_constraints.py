from typing import Iterable

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Collapsible, Label, Log, Static

from .base import AbstractMode


class UnsatisfiableConstraintsMode(Static, AbstractMode):

    mode_css = ""
    mode_name = "Unsatisfiable Constraints"
    mode_id = "unsat_constraints"
    order = 2

    def __init__(self, files: Iterable[str], log: Log):
        super().__init__()

    def compose(self) -> ComposeResult:
        yield VerticalScroll(Collapsible(Label("Some unsat constraint information"), title="UNSAT CONSTRAINT 1"))
