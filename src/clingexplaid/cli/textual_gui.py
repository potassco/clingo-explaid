"""
Module for a Command Line based GUI for clingexplaid
"""

import argparse
import asyncio
import itertools
import re
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple, Union, cast

import clingo
from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.containers import HorizontalScroll, Vertical, VerticalScroll
from textual.screen import Screen
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
from textual.widgets.tree import TreeNode

from ..mus import CoreComputer
from ..propagators import SolverDecisionPropagator
from ..propagators.propagator_solver_decisions import INTERNAL_STRING, Decision
from ..transformers import AssumptionTransformer, OptimizationRemover
from .textual_style import MAIN_CSS

MODE_MUS = "Minimal Unsatisfiable Subsets"
MODE_UNSAT_CONSTRAINTS = "Unsatisfiable Constraints"
MODE_SHOW_DECISIONS = "Show Decisions"
MODES = (
    MODE_MUS,
    MODE_UNSAT_CONSTRAINTS,
    MODE_SHOW_DECISIONS,
)
ACTIVE_CLASS = "active"


class ModelType(Enum):
    """
    Types of Model that can be found (Stable Model, MUS, ...)
    """

    MODEL = 1
    UNSAT_CONSTRAINT = 2
    MUS = 3


def read_file(path: Union[Path, str]) -> str:
    """
    Helper function to get the contents of a file as a string.
    """
    file_content = ""
    with open(path, "r", encoding="utf-8") as f:
        file_content = f.read()
    return file_content


def flatten_list(ls: Optional[List[List[Any]]]) -> List[Any]:
    """
    Helper function to flatten a list
    """
    if ls is None:
        ls = []
    return list(itertools.chain.from_iterable(ls))


def parse_constants(constant_strings: List[str]) -> Dict[str, str]:
    """
    Helper function to parse constants
    """
    constants = {}
    for const_string in constant_strings:
        result = re.search(r"(^[a-zA-Z_][a-zA-Z0-9_]*)=([a-zA-Z_][a-zA-Z0-9_]*|[0-9]+)$", const_string)
        if result is not None:
            constants[result.group(1)] = result.group(2)
    return constants


class SelectorWidget(Static):
    """SelectorWidget Field"""

    def __init__(self, compose_widgets: List[Widget], update_value_function: Callable[[Any], str]) -> None:
        super().__init__()
        self.compose_widgets = compose_widgets
        self.active = True
        self.value = ""
        self.update_value_function = update_value_function
        # this is used when the value of the checkbox is set by the system to avoid the changed event callback
        self.skip_checkbox_changed = False

        self.set_active_class()

    def set_active(self, active: bool) -> None:
        """
        Sets the active property to the provided value while updating the Selector's style
        """
        self.active = active
        self.skip_checkbox_changed = True
        self.query_one(Checkbox).value = active
        if self.active:
            self.apply_value_function()
        self.set_active_class()

    def apply_value_function(self) -> None:
        """
        Applies the on __init__ provided `update_value_function` to compute `SelectorWidget.value`
        """
        self.value = self.update_value_function(self)

    def set_active_class(self) -> None:
        """
        Sets the active class of the `SelectorWidget` according to `SelectorWidget.active`
        """
        if self.active:
            if ACTIVE_CLASS not in self.classes:
                self.add_class(ACTIVE_CLASS)
        else:
            self.remove_class(ACTIVE_CLASS)

    def compose(self) -> ComposeResult:
        """
        Composes the `SelectorWidget`'s components
        """
        yield Checkbox(value=True)
        yield from self.compose_widgets

    @on(Checkbox.Changed)
    async def selector_changed(self, event: Checkbox.Changed) -> None:
        """
        Callback for when the `SelectorWidget`'s Checkbox is changed.
        """
        # Updating the UI to show the reasons why validation failed
        if event.checkbox == self.query_one(Checkbox):
            if self.skip_checkbox_changed:
                self.skip_checkbox_changed = False
            else:
                self.active = event.checkbox.value
                self.set_active_class()
                await self.run_action("app.update_config")


class LabelInputWidget(SelectorWidget):
    """LabelInputWidget Field"""

    def __init__(self, name: str, value: str, update_value_function: Callable[[SelectorWidget], str]) -> None:
        super().__init__(
            compose_widgets=[
                Label(name),
                Input(placeholder="Value", value=value),
            ],
            update_value_function=update_value_function,
        )


class LabelWidget(SelectorWidget):
    """LabelWidget Field"""

    def __init__(self, path: str, update_value_function: Callable[[SelectorWidget], str]) -> None:
        super().__init__(
            compose_widgets=[
                HorizontalScroll(Label(path)),
            ],
            update_value_function=update_value_function,
        )


class SelectorList(Static):
    """Widget for selecting the program files"""

    def __init__(self, selectors: Optional[Iterable[Any]], classes: str = "") -> None:
        super().__init__(classes=classes)
        self.add_class("selectors")
        if selectors is None:
            selectors = []
        self.selectors = selectors

    def get_selectors(self) -> List[SelectorWidget]:
        """
        Base function for getting selectors. This should be overwritten in any classes that inherit from this class.
        """
        return []

    def compose(self) -> ComposeResult:
        """
        Composes the `SelectorList`'s components
        """
        yield VerticalScroll(
            *self.get_selectors(),
        )


class ConstantsWidget(SelectorList):
    """List Widget for Constants"""

    def __init__(self, constants: Optional[Dict[str, str]]) -> None:
        super().__init__(selectors={} if constants is None else constants)

    def get_selectors(self) -> List[SelectorWidget]:
        """
        Fill the `ConstantsWidget` with `LabelInputWidget`s for each constant.
        """
        return [
            LabelInputWidget(name, value, update_value_function=self.update_value)
            for name, value in dict(self.selectors).items()
        ]

    @staticmethod
    def update_value(selector_object: SelectorWidget) -> str:
        """
        Updates the value for each constant with its name and value
        """
        label_string = str(selector_object.query_one(Label).renderable).strip()
        input_string = str(selector_object.query_one(Input).value).strip()
        return f"#const {label_string}={input_string}."


class FilesWidget(SelectorList):
    """List Widget for Files"""

    def __init__(self, files: Optional[List[str]]) -> None:
        super().__init__(selectors=[] if files is None else files)

    def get_selectors(self) -> List[SelectorWidget]:
        """
        Fill the `FilesWidget` with `LabelWidget`s for each file.
        """
        return [LabelWidget(name, update_value_function=self.update_value) for name in self.selectors]

    @staticmethod
    def update_value(selector_object: SelectorWidget) -> str:
        """
        Updates the value for each file with its name
        """
        label_string = str(selector_object.query_one(Label).renderable).strip()
        return label_string


class SignaturesWidget(SelectorList):
    """List Widget for Signatures"""

    def __init__(self, signatures: Optional[List[str]]) -> None:
        super().__init__(selectors=[] if signatures is None else signatures)

    def get_selectors(self) -> List[SelectorWidget]:
        """
        Fill the `SignaturesWidget` with `LabelWidget`s for each signature.
        """
        return [LabelWidget(name, update_value_function=self.update_value) for name in self.selectors]

    @staticmethod
    def update_value(selector_object: SelectorWidget) -> str:
        """
        Updates the value for each file with its name and arity
        """
        label_string = str(selector_object.query_one(Label).renderable).strip()
        return label_string


class Sidebar(Static):
    """Widget for the clingexplaid sidebar"""

    def __init__(
        self,
        files: List[str],
        constants: Optional[Dict[str, str]],
        classes: str = "",
    ) -> None:
        super().__init__(classes=classes)
        self.files = files
        self.constants = {} if constants is None else constants
        self.signatures = self.get_all_program_signatures()

    def get_all_program_signatures(self) -> Set[Tuple[str, int]]:
        """
        Get all signatures occurring in all files provided.
        """
        # This is done with grounding rn but doing a text processing would probably be more efficient for large
        # programs!
        ctl = clingo.Control()
        for file in self.files:
            ctl.load(file)
        ctl.ground([("base", [])])
        return {(name, arity) for name, arity, _ in ctl.symbolic_atoms.signatures}

    def compose(self) -> ComposeResult:
        """
        Composes the `Sidebar`'s components
        """
        with TabbedContent():
            with TabPane("Files"):
                yield FilesWidget(self.files)
            with TabPane("Constants"):
                yield ConstantsWidget(self.constants)
            with TabPane("Signatures"):
                sorted_signatures = list(sorted(self.signatures, key=lambda x: x[0]))
                yield SignaturesWidget([INTERNAL_STRING] + [f"{name} / {arity}" for name, arity in sorted_signatures])


class ControlPanel(Static):
    """Widget for the clingexplaid sidebar"""

    def __init__(self, classes: str = ""):
        super().__init__(classes=classes)
        self.input_valid = True

    def compose(self) -> ComposeResult:
        """
        Composes the `ControlPanel`'s components
        """
        yield Label("Mode")
        yield Select(
            ((line, line) for line in MODES),
            allow_blank=False,
            id="mode-select",
        )
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

    @on(Select.Changed)
    async def select_changed(self, event: Select.Changed) -> None:
        """
        Callback for when the `ControlPanel`'s Mode Select is changed.
        """
        if event.select == self.query_one("#mode-select"):
            await self.run_action("app.update_mode")

    @on(Input.Changed)
    async def input_changed(self, event: Input.Changed) -> None:
        """
        Callback for when the `ControlPanel`'s Input is changed.
        """
        # Updating the UI to show the reasons why validation failed
        if event.input == self.query_one("#model-number-input"):
            if event.validation_result is None:
                return
            self.input_valid = event.validation_result.is_valid
            if not self.input_valid:
                self.add_class("error")
                first_error = event.validation_result.failure_descriptions[0]
                cast(Label, self.query_one("Label.error")).update(first_error)
            else:
                self.remove_class("error")
                cast(Label, self.query_one("Label.error")).update("")
                await self.run_action("app.update_config")

    @on(Input.Submitted)
    async def input_submitted(self, event: Input.Submitted) -> None:
        """
        Callback for when the `ControlPanel`'s Input is submitted.
        """
        if event.input == self.query_one("#model-number-input"):
            if self.input_valid:
                await self.run_action("app.solve")

    @on(Button.Pressed)
    async def solve(self, event: Button.Pressed) -> None:
        """
        Callback for when the `ControlPanel`'s Button is changed.
        """
        if event.button == self.query_one("#solve-button"):
            await self.run_action("app.solve")


class SolverTreeView(Static):
    """Widget for the clingexplaid show decisions tree"""

    def __init__(self, classes: str = "") -> None:
        super().__init__(classes=classes)
        self.solve_tree: Tree[str] = Tree("Solver Decisions", id="explanation-tree")

    def compose(self) -> ComposeResult:
        """
        Composes the `SolverTreeView`'s components
        """
        self.solve_tree.root.expand()
        yield self.solve_tree
        yield LoadingIndicator()


class ClingexplaidTextualApp(App[int]):
    """A textual app for a terminal GUI to use the clingexplaid functionality"""

    # pylint: disable=too-many-instance-attributes

    CSS = MAIN_CSS

    def __init__(self, files: List[str], constants: Dict[str, str]) -> None:
        super().__init__()
        self.files = files
        self.constants = constants
        self.tree_cursor: Optional[TreeNode[str]] = None
        self.model_count = 0

        self._selected_mode: Optional[str] = None
        self._config_model_number = 1
        self._config_show_internal = True
        self._loaded_files: Set[str] = set()
        self._loaded_signatures: Set[Tuple[str, int]] = set()

        self.bind("ctrl+x", "exit", description="Exit", key_display="CTRL+X")

    def compose(self) -> ComposeResult:
        """
        Composes the `ClingexplaidTextualApp`'s components
        """
        yield Vertical(
            ControlPanel(classes="box"),
            Sidebar(files=self.files, constants=self.constants, classes="box tabs"),
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

    async def on_model(self, model: List[str]) -> None:
        """
        Callback for when clingo finds a model.
        """
        self.model_count += 1
        if self.tree_cursor is None:
            return
        await self.add_model_node(" ".join(model), ModelType.MODEL)
        # add some small sleep time to make ux seem more interactive
        await asyncio.sleep(0.1)

    def on_propagate(self, decisions: List[Union[Decision, List[Decision]]]) -> None:
        """
        Callback for the registered propagator does a propagate step.
        """
        if self.tree_cursor is None:
            return
        for element in decisions:
            if isinstance(element, list):
                for literal in element:
                    if literal.matches_any(self._loaded_signatures, show_internal=self._config_show_internal):
                        entailment = self.tree_cursor.add_leaf(str(literal)).expand()
                        cast(Text, entailment.label).stylize("#666666")
            else:
                new_node = self.tree_cursor.add(str(element))
                new_node.expand()
                self.tree_cursor = new_node

    def on_undo(self) -> None:
        """
        Callback for the registered propagator does an undo step.
        """
        if self.tree_cursor is None:
            return
        undo = self.tree_cursor.add_leaf(f"UNDO {self.tree_cursor.label}")
        cast(Text, undo.label).stylize("#E53935")
        self.tree_cursor = self.tree_cursor.parent

    async def action_update_config(self) -> None:
        """
        Action to update the solving config
        """
        self.refresh_bindings()

        # update model number
        model_number_input = cast(Input, self.query_one("#model-number-input"))
        model_number = int(model_number_input.value)
        self._config_model_number = model_number

        # update loaded files
        files_widget = self.query_one(FilesWidget)
        files = set()
        for selector in files_widget.query(SelectorWidget):
            selector.apply_value_function()
            if selector.active:
                files.add(selector.value)
        self._loaded_files = files

        # update program signatures
        signatures_widget = self.query_one(SignaturesWidget)
        signature_strings = set()
        for selector in signatures_widget.query(SelectorWidget):
            selector.apply_value_function()
            if selector.active:
                signature_strings.add(selector.value)
        signatures = set()
        self._config_show_internal = False
        for signature_string in signature_strings:
            if signature_string.startswith(INTERNAL_STRING):
                self._config_show_internal = True
            else:
                name, arity = signature_string.split(" / ")
                signatures.add((name, int(arity)))
        self._loaded_signatures = signatures

    async def action_mode_mus(self) -> None:
        """
        Action for MUS Mode
        """
        if not self._loaded_files:
            # TODO: Maybe raise an exception here?
            return

        ctl = clingo.Control()

        # transform matching facts to choices to allow assumptions
        at = AssumptionTransformer(signatures=self._loaded_signatures)
        program_transformed = at.parse_files(list(self._loaded_files))

        # remove optimization statements
        opt_rm = OptimizationRemover()
        program_no_opt = opt_rm.parse_string(program_transformed)

        ctl.add("base", [], program_no_opt)
        ctl.ground([("base", [])])

        # get assumption set
        assumptions = at.get_assumption_literals(ctl)
        # TODO: add program constants
        #  get_constant_string(c, v, prefix="-c ") for c, v in self.argument_constants.items()

        cc = CoreComputer(ctl, assumptions)

        # check if the program is unsat
        program_unsat = False
        with ctl.solve(assumptions=list(assumptions), yield_=True) as solve_handle:
            if not solve_handle.get().satisfiable:
                program_unsat = True
        if not program_unsat:
            if self.tree_cursor is None:
                return
            self.tree_cursor.add_leaf("SATISFIABLE PROGRAM")
            return

        for mus in cc.get_multiple_minimal(max_mus=self._config_model_number):
            self.model_count += 1
            mus_string = " ".join(cc.mus_to_string(mus))
            await self.add_model_node(mus_string, ModelType.MUS)

        if not self.model_count:
            if self.tree_cursor is None:
                return
            self.tree_cursor.add_leaf(
                "NO MUS CONTAINED: The unsatisfiability of this program is not induced by the provided assumptions"
            )

    async def action_mode_unsat_constraints(self) -> None:
        """
        Action for Unsat Constraints Mode
        """
        return None

    async def action_mode_show_decisions(self) -> None:
        """
        Action for Show Decisions Mode
        """
        sdp = SolverDecisionPropagator(
            callback_propagate=self.on_propagate,
            callback_undo=self.on_undo,
        )
        ctl = clingo.Control(f"{self._config_model_number}")
        ctl.register_propagator(sdp)
        for file in self._loaded_files:
            ctl.load(file)
        if not self._loaded_files:
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
                    await self.on_model([str(a) for a in model.symbols(atoms=True)])
                exhausted = result.exhausted
                if not exhausted:
                    solver_handle.resume()

        await self.reset_tree_cursor()
        end_string = "SAT" if self.model_count > 0 else "UNSAT"
        if self.tree_cursor is None:
            return
        self.tree_cursor.add(end_string)

    async def action_solve(self) -> None:
        """
        Action to exit the textual application
        """
        self.refresh_bindings()

        tree_view = self.query_one(SolverTreeView)
        tree = tree_view.solve_tree
        await self.reset_solve_tree(str(tree.root.label))

        solve_button = self.query_one("#solve-button")

        self.model_count = 0

        solve_button.disabled = True
        tree_view.add_class("solving")

        if self._selected_mode == MODE_MUS:
            await self.action_mode_mus()
        elif self._selected_mode == MODE_UNSAT_CONSTRAINTS:
            pass
        elif self._selected_mode == MODE_SHOW_DECISIONS:
            await self.action_mode_show_decisions()

        tree_view.remove_class("solving")
        solve_button.disabled = False

        await self.reset_tree_cursor()

    async def action_update_mode(self) -> None:
        """
        Action that updates the currently selected mode
        """
        selected_mode = cast(Select[str], self.query_one("#mode-select")).value
        self._selected_mode = str(selected_mode)
        if selected_mode == MODE_MUS:
            self.set_mode_class(self.query_one(Screen), "mode-mus")
            await self.set_all_selectors(self.query_one(SignaturesWidget), False)
            await self.reset_solve_tree("Minimal Unsatisfiable Subsets")
        elif selected_mode == MODE_UNSAT_CONSTRAINTS:
            self.set_mode_class(self.query_one(Screen), "mode-unsat-constraints")
            await self.reset_solve_tree("Unsatisfiable Constraints")
        elif selected_mode == MODE_SHOW_DECISIONS:
            self.set_mode_class(self.query_one(Screen), "mode-show-decisions")
            await self.set_all_selectors(self.query_one(SignaturesWidget), True)
            await self.reset_solve_tree("Solver Decisions")

    async def action_debug(self, msg: str) -> None:
        """
        Action to add a leaf with custom message to the solve tree for debugging purposes
        """
        if self.tree_cursor is None:
            # TODO: Extract this into a function that does this once so I don't have to do it always >:(
            return
        self.tree_cursor.add_leaf(f"DEBUG: {msg}")

    @staticmethod
    def set_mode_class(widget: Widget, mode_class: str) -> None:
        """
        Sets the provided mode class on the provided widget
        """
        mode_classes = [c for c in widget.classes if c.startswith("mode-")]
        for c in mode_classes:
            widget.remove_class(c)
        widget.add_class(mode_class)

    @staticmethod
    async def set_all_selectors(parent: Widget, value: bool) -> None:
        """
        Sets the values of all SelectorWidgets under the provided parent to value
        """
        for selector in parent.query(SelectorWidget):
            selector.set_active(value)
            selector.skip_checkbox_changed = False

    async def add_model_node(self, value: str, model_type: ModelType) -> None:
        """
        Adds a model node of type model_type to the solver tree
        """
        match model_type:
            case ModelType.MODEL:
                color_fg, color_bg_1, color_bg_2 = ("#000000", "#CCCCCC", "#999999")
            case ModelType.UNSAT_CONSTRAINT:
                color_fg, color_bg_1, color_bg_2 = ("#f27573", "#7c1313", "#610f0f")
            case ModelType.MUS:
                color_fg, color_bg_1, color_bg_2 = ("#66bdff", "#004578", "#003761")
            case _:
                raise ValueError("Model type not supported")

        model_name = model_type.name.replace("_", " ")
        if self.tree_cursor is None:
            # TODO: again extract this !!!
            return
        model_node = self.tree_cursor.add_leaf(f" {model_name}  {self.model_count}  {value}")
        cast(Text, model_node.label).stylize(f"{color_fg} on {color_bg_1}", 0, len(model_name) + 2)
        cast(Text, model_node.label).stylize(
            f"{color_fg} on {color_bg_2}", len(model_name) + 2, len(model_name) + 4 + len(str(self.model_count))
        )

    async def reset_tree_cursor(self) -> None:
        """
        Resets the tree cursor to the SolverTree root
        """
        tree_view = self.query_one(SolverTreeView)
        tree = tree_view.solve_tree
        self.tree_cursor = tree.root

    async def reset_solve_tree(self, new_root_name: str) -> None:
        """
        Resets the SolverTree
        """
        tree_view = self.query_one(SolverTreeView)
        tree = tree_view.solve_tree
        tree.reset(new_root_name)
        self.tree_cursor = tree.root

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        """
        Check if any action may run
        """
        return True


def textual_main() -> None:
    """
    Main function for the clingo-explaid textual app. This function includes a dedicated ArgumentParser
    """

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
    )
    app.run()
