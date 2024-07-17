from typing import Iterable

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Collapsible, Label, Log, Static

from .base import AbstractMode


class MinimalUnsatisfiableSubsetMode(Static, AbstractMode):

    mode_css = ""
    mode_name = "Minimal Unsatisfiable Subsets"
    mode_id = "mus"
    order = 1

    def __init__(self, files: Iterable[str], log: Log):
        super().__init__()

    def compose(self) -> ComposeResult:
        yield VerticalScroll(Collapsible(Label("Some MUS information"), title="MUS 1"))
