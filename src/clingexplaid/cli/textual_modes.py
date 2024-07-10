from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Collapsible, Label, Static


class SolvingMode(Static):

    def compose(self) -> ComposeResult:
        yield VerticalScroll(Collapsible(Label("Some model information"), title="Model 1"))
