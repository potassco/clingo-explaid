"""
Module for a Command Line based GUI for clingexplaid
"""

import argparse
import asyncio
import itertools
import re
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple, Union

import clingo
from textual import on
from textual.app import App, ComposeResult
from textual.containers import HorizontalScroll, Vertical, VerticalScroll
from textual.validation import Number
from textual.widget import Widget
from textual.widgets import (
    Button,
    Checkbox,
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

from ..propagators import SolverDecisionPropagator
from ..propagators.propagator_solver_decisions import INTERNAL_STRING
from .textual_style import MAIN_CSS

ACTIVE_CLASS = "active"


class SelectorWidget(Static):
    """SelectorWidget Field"""

    def __init__(self, compose_widgets: List[Widget], update_value_function: Callable) -> None:
        super(SelectorWidget, self).__init__()
        self.compose_widgets = compose_widgets
        self.active = True
        self.value = ""
        self.update_value_function = update_value_function

        self.set_active_class()

    def toggle_active(self) -> None:
        self.active = not self.active
        if self.active:
            self.apply_value_function()
        self.set_active_class()

    def apply_value_function(self):
        self.value = self.update_value_function(self)

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

    @on(Checkbox.Changed)
    async def selector_changed(self, event: Checkbox.Changed) -> None:
        # Updating the UI to show the reasons why validation failed
        if event.checkbox == self.query_one(Checkbox):
            self.toggle_active()
            await self.run_action("update_config")


class LabelInputWidget(SelectorWidget):
    """LabelInputWidget Field"""

    def __init__(self, name: str, value: str, update_value_function: Callable) -> None:
        super(LabelInputWidget, self).__init__(
            compose_widgets=[
                Label(name),
                Input(placeholder="Value", value=value),
            ],
            update_value_function=update_value_function,
        )


class LabelWidget(SelectorWidget):
    """LabelWidget Field"""

    def __init__(self, path: str, update_value_function: Callable) -> None:
        super(LabelWidget, self).__init__(
            compose_widgets=[
                HorizontalScroll(Label(path)),
            ],
            update_value_function=update_value_function,
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
        return [
            LabelInputWidget(name, value, update_value_function=self.update_value)
            for name, value in dict(self.selectors).items()
        ]

    @staticmethod
    def update_value(selector_object):
        label_string = str(selector_object.query_one(Label).renderable).strip()
        input_string = str(selector_object.query_one(Input).value).strip()
        return f"#const {label_string}={input_string}."


class FilesWidget(SelectorList):

    def __init__(self, files: Optional[List[str]]) -> None:
        super(FilesWidget, self).__init__(selectors=[] if files is None else files)

    def get_selectors(self) -> List[LabelWidget]:
        return [LabelWidget(name, update_value_function=self.update_value) for name in self.selectors]

    @staticmethod
    def update_value(selector_object):
        label_string = str(selector_object.query_one(Label).renderable).strip()
        return label_string


class SignaturesWidget(SelectorList):

    def __init__(self, signatures: Optional[List[str]]) -> None:
        super(SignaturesWidget, self).__init__(selectors=[] if signatures is None else signatures)

    def get_selectors(self) -> List[LabelWidget]:
        return [LabelWidget(name, update_value_function=self.update_value) for name in self.selectors]

    @staticmethod
    def update_value(selector_object):
        label_string = str(selector_object.query_one(Label).renderable).strip()
        return label_string


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
        self.signatures = self.get_all_program_signatures()

    def get_all_program_signatures(self) -> Set[Tuple[str, int]]:
        # TODO: This is done with grounding rn but doing a text processing would probably be more efficient for large
        #  programs!
        ctl = clingo.Control()
        for file in self.files:
            ctl.load(file)
        ctl.ground([("base", [])])
        return {(name, arity) for name, arity, _ in ctl.symbolic_atoms.signatures}

    def compose(self) -> ComposeResult:
        with TabbedContent():
            with TabPane("Files"):
                yield FilesWidget(self.files)
            with TabPane("Constants"):
                yield ConstantsWidget(self.constants)
            with TabPane("Decision Signatures"):
                sorted_signatures = list(sorted(self.signatures, key=lambda x: x[0]))
                yield SignaturesWidget([INTERNAL_STRING] + [f"{name} / {arity}" for name, arity in sorted_signatures])


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
            id="model-number-input",
        )
        yield Static(classes="error")
        yield Label("", classes="error")
        yield Button("SOLVE", id="solve-button", variant="primary")

    @on(Input.Changed)
    async def input_changed(self, event: Input.Changed) -> None:
        # Updating the UI to show the reasons why validation failed
        if event.input == self.query_one("#model-number-input"):
            if not event.validation_result.is_valid:
                self.add_class("error")
                first_error = event.validation_result.failure_descriptions[0]
                self.query_one("Label.error").update(first_error)
            else:
                self.remove_class("error")
                self.query_one("Label.error").update("")
                await self.run_action("update_config")

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
        self.solve_tree.root.expand()
        yield self.solve_tree
        yield LoadingIndicator()


def read_file(path: Union[Path, str]) -> str:
    file_content = ""
    with open(path, "r", encoding="utf-8") as f:
        file_content = f.read()
    return file_content


class ClingexplaidTextualApp(App[int]):
    """A textual app for a terminal GUI to use the clingexplaid functionality"""

    BINDINGS = [
        ("ctrl+x", "exit", "Exit"),
        # ("ctrl+s", "solve", "Solve"),
    ]
    CSS = MAIN_CSS

    def __init__(self, files: List[str], constants: Dict[str, str], signatures: Set[Tuple[str, int]]) -> None:
        super(ClingexplaidTextualApp, self).__init__()
        self.files = files
        self.constants = constants
        self.signatures = signatures
        self.tree_cursor = None
        self.model_count = 0

        self.config_model_number = 1
        self.config_show_internal = True
        self.loaded_files = set()
        self.loaded_signatures = set()

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

    async def on_model(self, model):
        self.model_count += 1
        model = self.tree_cursor.add_leaf(f" MODEL  {self.model_count}  {' '.join([str(a) for a in model])}")
        model.label.stylize("#000000 on #CCCCCC", 0, 7)
        model.label.stylize("#000000 on #999999", 7, 7 + 2 + len(str(self.model_count)))
        # add some small sleep time to make ux seem more interactive
        await asyncio.sleep(0.5)

    def on_propagate(self, decisions):
        for element in decisions:
            if isinstance(element, list):
                for literal in element:
                    if literal.matches_any(self.loaded_signatures, show_internal=self.config_show_internal):
                        entailment = self.tree_cursor.add_leaf(str(literal)).expand()
                        entailment.label.stylize("#666666")
            else:
                new_node = self.tree_cursor.add(str(element))
                new_node.expand()
                self.tree_cursor = new_node

    def on_undo(self):
        undo = self.tree_cursor.add_leaf(f"UNDO {self.tree_cursor.label}")
        undo.label.stylize("#E53935")
        self.tree_cursor = self.tree_cursor.parent

    async def action_update_config(self) -> None:
        """
        Action to update the solving config
        """
        # update model number
        model_number_input = self.query_one("#model-number-input")
        model_number = int(model_number_input.value)
        self.config_model_number = model_number

        # update loaded files
        files_widget = self.query_one(FilesWidget)
        files = set()
        for selector in files_widget.query(SelectorWidget):
            selector.apply_value_function()
            if selector.active:
                files.add(selector.value)
        self.loaded_files = files

        # update program signatures
        signatures_widget = self.query_one(SignaturesWidget)
        signature_strings = set()
        for selector in signatures_widget.query(SelectorWidget):
            selector.apply_value_function()
            if selector.active:
                signature_strings.add(selector.value)
        signatures = set()
        self.config_show_internal = False
        for signature_string in signature_strings:
            if signature_string.startswith(INTERNAL_STRING):
                self.config_show_internal = True
            else:
                name, arity = signature_string.split(" / ")
                signatures.add((name, int(arity)))
        self.loaded_signatures = signatures

    async def action_solve(self) -> None:
        """
        Action to exit the textual application
        """
        tree_view = self.query_one(SolverTreeView)
        solve_button = self.query_one("#solve-button")

        tree = tree_view.solve_tree
        tree.reset(tree.root.label)
        self.tree_cursor = tree.root
        self.model_count = 0

        solve_button.disabled = True
        tree_view.add_class("solving")

        sdp = SolverDecisionPropagator(
            callback_propagate=self.on_propagate,
            callback_undo=self.on_undo,
        )
        ctl = clingo.Control(f"{self.config_model_number}")
        ctl.register_propagator(sdp)
        for file in self.loaded_files:
            ctl.load(file)
        if not self.loaded_files:
            ctl.add("base", [], "")
        ctl.ground([("base", [])])

        exhausted = False

        with ctl.solve(yield_=True) as solver_handle:
            while not exhausted:
                result = solver_handle.get()
                if result.satisfiable:
                    model = solver_handle.model()
                    if model is None:
                        break
                    await self.on_model(model.symbols(atoms=True))
                exhausted = result.exhausted
                if not exhausted:
                    solver_handle.resume()
        tree_view.remove_class("solving")
        solve_button.disabled = False

        self.tree_cursor = tree.root
        end_string = "SAT" if self.model_count > 0 else "UNSAT"
        self.tree_cursor.add(end_string)


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
        files=list(set(flatten_list(args.files))),
        constants=parse_constants(flatten_list(args.const)),
        signatures=parse_signatures(flatten_list(args.decision_signature)),
    )
    app.run()
