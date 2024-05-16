"""
Module for a Command Line based GUI for clingexplaid
"""

import argparse
import asyncio
import itertools
import re
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from textual import on
from textual.app import App, ComposeResult
from textual.containers import HorizontalScroll, Vertical, VerticalScroll
from textual.validation import Number
from textual.widget import Widget
from textual.widgets import (
    Button,
    Checkbox,
    Collapsible,
    Footer,
    Input,
    Label,
    LoadingIndicator,
    Select,
    Static,
    TabbedContent,
    TabPane,
    Tree,
)

ACTIVE_CLASS = "active"


class SelectorWidget(Static):
    """SelectorWidget Field"""

    def __init__(self, compose_widgets: List[Widget]) -> None:
        super(SelectorWidget, self).__init__()
        self.compose_widgets = compose_widgets
        self.active = True
        self.set_active_class()

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        self.toggle_active()

    def toggle_active(self) -> None:
        self.active = not self.active
        self.set_active_class()

    def set_active_class(self):
        if self.active:
            if ACTIVE_CLASS not in self.classes:
                self.add_class(ACTIVE_CLASS)
        else:
            self.remove_class(ACTIVE_CLASS)

    def compose(self) -> ComposeResult:
        yield Checkbox(value=True)
        for element in self.compose_widgets:
            yield element


class LabelInputWidget(SelectorWidget):
    """LabelInputWidget Field"""

    def __init__(self, name: str, value: str) -> None:
        super(LabelInputWidget, self).__init__(
            compose_widgets=[
                Label(name),
                Input(placeholder="Value", value=value),
            ]
        )


class LabelWidget(SelectorWidget):
    """LabelWidget Field"""

    def __init__(self, path: str) -> None:
        super(LabelWidget, self).__init__(
            compose_widgets=[
                HorizontalScroll(Label(path)),
            ]
        )


class SelectorList(Static):
    """Widget for selecting the program files"""

    def __init__(self, selectors: Optional[Iterable], classes: str = "") -> None:
        super(SelectorList, self).__init__(classes=classes)
        self.add_class("selectors")
        if selectors is None:
            selectors = []
        self.selectors = selectors

    def get_selectors(self) -> List[SelectorWidget]:
        return []

    def compose(self) -> ComposeResult:
        yield VerticalScroll(
            *self.get_selectors(),
        )


class ConstantsWidget(SelectorList):

    def __init__(self, constants: Optional[Dict[str, str]]) -> None:
        super(ConstantsWidget, self).__init__(selectors={} if constants is None else constants)

    def get_selectors(self) -> List[LabelInputWidget]:
        return [LabelInputWidget(name, value) for name, value in dict(self.selectors).items()]


class FilesWidget(SelectorList):

    def __init__(self, files: Optional[List[str]]) -> None:
        super(FilesWidget, self).__init__(selectors=[] if files is None else files)

    def get_selectors(self) -> List[LabelWidget]:
        return [LabelWidget(name) for name in self.selectors]


class SignaturesWidget(SelectorList):

    def __init__(self, signatures: Optional[List[str]]) -> None:
        super(SignaturesWidget, self).__init__(selectors=[] if signatures is None else signatures)

    def get_selectors(self) -> List[LabelWidget]:
        return [LabelWidget(name) for name in self.selectors]


class Sidebar(Static):
    """Widget for the clingexplaid sidebar"""

    def __init__(
        self,
        files: List[str],
        constants: Optional[Dict[str, str]],
        signatures: Optional[Set[Tuple[str, int]]],
        classes: str = "",
    ) -> None:
        super(Sidebar, self).__init__(classes=classes)
        self.files = files
        self.constants = {} if constants is None else constants
        self.signatures = set() if signatures is None else signatures

    def compose(self) -> ComposeResult:
        with TabbedContent():
            with TabPane("Files"):
                yield FilesWidget(self.files)
            with TabPane("Constants"):
                yield ConstantsWidget(self.constants)
            with TabPane("Decision Signatures"):
                yield SignaturesWidget([f"{name} / {arity}" for name, arity in self.signatures])


class ControlPanel(Static):
    """Widget for the clingexplaid sidebar"""

    def compose(self) -> ComposeResult:
        yield Label("Mode")
        yield Select(((line, line) for line in ["SHOW DECISIONS"]), allow_blank=False)
        yield Label("Models")
        yield Input(
            placeholder="Number",
            type="number",
            value="1",
            validate_on=["changed"],
            validators=[Number(minimum=0)],
        )
        yield Static(classes="error")
        yield Label("", classes="error")
        yield Button("SOLVE", id="solve-button", variant="primary")

    @on(Input.Changed)
    def show_invalid_reasons(self, event: Input.Changed) -> None:
        # Updating the UI to show the reasons why validation failed
        if not event.validation_result.is_valid:
            self.add_class("error")
            first_error = event.validation_result.failure_descriptions[0]
            self.query_one("Label.error").update(first_error)
        else:
            self.remove_class("error")
            self.query_one("Label.error").update("")

    @on(Button.Pressed)
    async def solve(self, event: Button.Pressed) -> None:
        if event.button == self.query_one("#solve-button"):
            await self.run_action("solve")


class SolverTreeView(Static):
    """Widget for the clingexplaid show decisions tree"""

    def __init__(self, classes: str = "") -> None:
        super(SolverTreeView, self).__init__(classes=classes)
        self.solve_tree = Tree("Solver Decisions", id="explanation-tree")

    def compose(self) -> ComposeResult:
        self.solve_tree.root.add("Test 1")
        self.solve_tree.root.add("Test 2")
        self.solve_tree.root.add("Test 3")
        self.solve_tree.root.expand()
        yield self.solve_tree
        yield LoadingIndicator()


class ClingexplaidTextualApp(App[int]):
    """A textual app for a terminal GUI to use the clingexplaid functionality"""

    BINDINGS = [
        ("ctrl+x", "exit", "Exit"),
        ("ctrl+s", "solve", "Solve"),
    ]
    CSS = """
    Screen {
        layout: grid;
        grid-size: 2 2;
        grid-columns: 1fr 2fr;
        grid-rows: 1fr auto;
    }
    #debug{
        column-span: 2;
    }

    .box {
        height: 100%;
        border: round #455A64;
        padding: 1;
    }

    .box.tabs{
        padding: 0;
    }

    #top-cell {
        layout: grid;
        grid-size: 1;
        grid-rows: auto 1fr;
    }

    ControlPanel {
        layout: grid;
        grid-size: 2;
        grid-columns: auto 1fr;
        grid-gutter: 1;
    }

    ControlPanel Input{
        width: 100%;
    }

    ControlPanel Label {
        padding: 1 2;
        background: #263238;
        width: 100%;
    }

    ControlPanel Label.error{
        border: tall rgb(235,64,52);
        background: rgba(235,64,52,0.2);
        padding: 0 2;
        color: rgb(235,64,52);
    }

    ControlPanel .error{
        display: none;
    }

    ControlPanel.error .error{
        display: block
    }

    ControlPanel #solve-button{
        column-span: 2;
        width: 100%;
    }

    ControlPanel.error #solve-button{
        display: none;
    }

    .selectors{
        background: #000;
    }

    SelectorWidget{
        layout: grid;
        grid-size: 2;
        grid-columns: auto 1fr;
    }

    LabelInputWidget{
        layout: grid;
        grid-size: 3;
        grid-columns: auto 1fr 1fr;
    }

    SelectorWidget{
        background: transparent;
    }

    SelectorWidget.active{
        background: $primary-darken-3;
    }

    SelectorWidget Label{
        padding: 1;
    }

    SelectorWidget Checkbox{
        background: transparent;
    }

    SelectorWidget Input{
        border: none;
        padding: 1 2;
    }

    SelectorWidget HorizontalScroll{
        height: auto;
        background: transparent;
    }

    SolverTreeView{
        content-align: center middle;
    }

    SolverTreeView Tree{
        display: block;
        padding: 1 2;
    }

    SolverTreeView.loading Tree{
        display: none;
    }

    SolverTreeView LoadingIndicator{
        display: none;
    }

    SolverTreeView.loading LoadingIndicator{
        display: block;
        height: 20;
    }
    """

    def __init__(self, files: List[str], constants: Dict[str, str], signatures: Set[Tuple[str, int]]) -> None:
        super(ClingexplaidTextualApp, self).__init__()
        self.files = files
        self.constants = constants
        self.signatures = signatures

    def compose(self) -> ComposeResult:
        yield Vertical(
            ControlPanel(classes="box"),
            Sidebar(files=self.files, constants=self.constants, signatures=self.signatures, classes="box tabs"),
            id="top-cell",
        )
        yield VerticalScroll(
            SolverTreeView(),
            classes="box",
        )
        yield Label(id="debug")
        yield Footer()

    def action_exit(self) -> None:
        """
        Action to exit the textual application
        """
        self.exit(0)

    async def action_solve(self) -> None:
        """
        Action to exit the textual application
        """
        tree_view = self.query_one(SolverTreeView)
        solve_button = self.query_one("#solve-button")
        tree = tree_view.solve_tree
        tree.reset(tree.root.label)
        tree_view.add_class("loading")
        # deactivate solve button
        solve_button.disabled = True
        await asyncio.sleep(2)
        solve_button.disabled = False
        tree_view.remove_class("loading")
        tree.root.add("TEST")


def flatten_list(ls: Optional[List[List[Any]]]) -> List:
    if ls is None:
        ls = []
    return list(itertools.chain.from_iterable(ls))


def parse_constants(constant_strings: List[str]) -> Dict[str, str]:
    constants = {}
    for const_string in constant_strings:
        result = re.search(r"(^[a-zA-Z_][a-zA-Z0-9_]*)=([a-zA-Z_][a-zA-Z0-9_]*|[0-9]+)$", const_string)
        if result is not None:
            constants[result.group(1)] = result.group(2)
    return constants


def parse_signatures(signature_strings: List[str]) -> Set[Tuple[str, int]]:
    signatures = set()
    for signature_string in signature_strings:
        result = re.search(r"^([a-zA-Z_][a-zA-Z0-9_]*)/([0-9]+)$", signature_string)
        if result is not None:
            signatures.add((result.group(1), int(result.group(2))))
    return signatures


def textual_main():
    parser = argparse.ArgumentParser(prog="clingexplaid", description="What the program does", epilog="Epilog Text")
    parser.add_argument(
        "files",
        type=str,
        nargs="+",
        action="append",
        help="All logic program files",
    )
    parser.add_argument(
        "-c",
        "--const",
        type=str,
        nargs="*",
        action="append",
        help="Specifies a clingo constant value",
    )
    parser.add_argument(
        "-d",
        "--decision-signature",
        type=str,
        nargs="*",
        action="append",
        help="Defines shown signatures in solver decision tree",
    )
    args = parser.parse_args()

    app = ClingexplaidTextualApp(
        files=flatten_list(args.files),
        constants=parse_constants(flatten_list(args.const)),
        signatures=parse_signatures(flatten_list(args.decision_signature)),
    )
    app.run()
