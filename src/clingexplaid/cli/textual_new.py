from dataclasses import dataclass
from typing import AsyncGenerator, Dict, Iterable, List, Optional

import clingo
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.events import Compose, Load, Mount
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Button, Checkbox, Collapsible, Footer, Label, Log, Select, Static, TextArea

from .textual_style_new import MAIN_CSS
from .util import StableModel


class CoolCheckbox(Checkbox):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.BUTTON_INNER = " ● "
        self.BUTTON_LEFT = ""
        self.BUTTON_RIGHT = ""


class Header(Static):

    def compose(self) -> ComposeResult:
        yield Label("SAT", id="sat-indicator")
        yield Static()
        yield Button("Select All", id="select-all-button")
        yield Button("Clear Selection", id="clear-selection-button")

    @on(Button.Pressed)
    async def button_pressed(self, event: Button.Pressed) -> None:
        if event.button == self.query_one("#select-all-button"):
            await self.run_action("app.models_select_all()")
        elif event.button == self.query_one("#clear-selection-button"):
            await self.run_action("app.models_select_clear()")


class SolverActions(Static):

    models_exhausted = reactive(False, recompose=True)

    def compose(self) -> ComposeResult:
        yield Button("Last", disabled=self.models_exhausted)
        yield Button("Next", disabled=self.models_exhausted, id="models-next-button")
        yield Button("All", disabled=self.models_exhausted, id="models-all-button")

    @on(Button.Pressed)
    async def button_pressed(self, event: Button.Pressed) -> None:
        if event.button == self.query_one("#models-next-button"):
            await self.run_action("app.models_find_next()")
        elif event.button == self.query_one("#models-all-button"):
            await self.run_action("app.models_find_all()")


class Model(Static):

    def __init__(self, model: StableModel, selected: bool = False):
        super().__init__()
        self._model = model
        self._model_id = model.model_id
        self._skip_next_checkbox_change = False
        self.collapsed: bool = False
        self.selected: bool = selected
        self.cost: Optional[Iterable[int]] = model.cost
        self.optimal: bool = model.optimal

        if model.optimal:
            self.add_class("optimal")
        if self.selected:
            self.add_class("selected")

    def compose(self) -> ComposeResult:
        yield Collapsible(
            Collapsible(Label(" ".join([str(s) for s in self._model.atoms])), title="Shown Atoms", classes="result"),
            title=f"Model {self._model_id}",
            collapsed=self.collapsed,
        )
        yield ModelHeader(self)

    def set_selected(self, selected: bool, update_checkbox: bool = False):
        self.selected = selected
        if selected:
            self.add_class("selected")
        else:
            self.remove_class("selected")
        if update_checkbox:
            # Update Checkbox value if its value differs from the target value
            checkbox = self.query_one(Checkbox)
            if checkbox.value != selected:
                self._skip_next_checkbox_change = True
                checkbox.value = selected

    def get_model_id(self) -> int:
        return self._model_id

    def toggle_selected(self):
        self.set_selected(not self.selected)

    @on(Checkbox.Changed)
    def checkbox_changed(self, event: Checkbox.Changed) -> None:
        if event.checkbox == self.query_one(Checkbox):
            if self._skip_next_checkbox_change:
                self._skip_next_checkbox_change = False
                return
            self.toggle_selected()


class ModelHeader(Static):

    def __init__(self, model: Model):
        super().__init__()
        self._model = model
        self._cost = model.cost
        self._optimal = model.optimal

    def compose(self) -> ComposeResult:
        # COST LABELS
        cost_labels = []
        if self._cost is not None:
            for cost in self._cost:
                cost_labels.append(Label(str(cost), classes="model-cost"))
        yield Horizontal(*cost_labels, classes="costs")
        # OPTIMALITY LABEL
        optimal_label = Label(f"⭐", classes="optimality-indicator hidden")
        if self._optimal:
            optimal_label.remove_class("hidden")
        yield optimal_label
        # SELECTION CHECKBOX
        yield CoolCheckbox(classes="model-selector")
        yield Static()


class Filters(Static):

    def compose(self) -> ComposeResult:
        yield CoolCheckbox("All Atoms")
        yield CoolCheckbox("Shown Atoms", value=True)
        yield CoolCheckbox("Theory Atoms")


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


@dataclass
class BindingAction:
    keys: str
    keys_display: Optional[str]
    description: Optional[str]
    active: bool = True


class ClingexplaidTextualApp(App[int]):
    """A textual app for a terminal GUI to use the clingexplaid functionality"""

    CSS = MAIN_CSS

    class ModelsExhausted(Message):
        """The Model-Search-Space was exhausted"""

    def __init__(self, files: List[str], constants: Dict[str, str]) -> None:
        super().__init__()

        self.files: List[str] = files
        self.constants: Dict[str, str] = constants

        self._program_satisfiability = self._check_satisfiability()
        self._control = clingo.Control()
        if self.files:
            for file in self.files:
                self._control.load(file)
        else:
            self._control.load("-")
        self._control.ground([("base", [])])

        self._model_generator = self.get_models()
        self._models = set()

        self.actions = {
            "exit": BindingAction(keys="ctrl+x", keys_display="CTRL+X", description="Exit"),
            "models_find_next": BindingAction(keys="ctrl+n", keys_display="CTRL+N", description="Next Model"),
            "models_find_all": BindingAction(keys="ctrl+a", keys_display="CTRL+A", description="All Models"),
        }
        for name, action in self.actions.items():
            self.bind(action.keys, name, description=action.description, key_display=action.keys_display)

    def compose(self) -> ComposeResult:
        """
        Composes the `ClingexplaidTextualApp`'s components
        """
        log = Log()
        log.write("DEBUG\n")

        yield Vertical(Header(), SolverActions(), Models(self), Actions(), id="content")
        yield log
        yield Footer()

    @on(Mount)
    async def initialization(self) -> None:
        # load first model when application is initialized
        await self.run_action("app.models_find_next()")

    @on(ModelsExhausted)
    def on_models_exhausted(self):
        # disable action bindings for model finding actions
        for action in self.actions.keys():
            if not action.startswith("models_find_"):
                continue
            self.actions[action].active = False
        self.refresh_bindings()
        self.query_one(SolverActions).models_exhausted = True
        self.query_one(Log).write("MODELS EXHAUSTED\n")

    async def get_models(self) -> AsyncGenerator[StableModel, None]:
        self._control.configuration.solve.models = 0
        self._control.configuration.solve.opt_mode = "optN"
        with self._control.solve(yield_=True) as solve_handle:
            exhausted = False
            while True:
                self.query_one(Log).write(
                    f"[{solve_handle.model().cost}][{solve_handle.model().optimality_proven}] model [{[s for s in solve_handle.model().symbols(atoms=True)]}] {solve_handle.get().satisfiable} {solve_handle.get().exhausted}\n"
                )
                stable_model = StableModel(
                    model_id=len(self._models) + 1,
                    model=solve_handle.model(),
                    cost=solve_handle.model().cost,
                    optimal=solve_handle.model().optimality_proven,
                )
                solve_handle.resume()

                yield_model = True
                if solve_handle.model() is not None:
                    # If the next stable model is optimal and the current model is not.
                    # In clingo the first optimal model is found twice so we skip the first one
                    if stable_model.optimal != solve_handle.model().optimality_proven:
                        yield_model = False

                if solve_handle.get().exhausted:
                    exhausted = True
                    # After search space is exhausted post appropriate message
                    self.post_message(self.ModelsExhausted())

                if yield_model:
                    yield stable_model
                if exhausted:
                    break

    async def action_exit(self) -> None:
        """
        Action to exit the textual application
        """
        self.exit(0)

    async def action_models_select_all(self):
        for model in self.query(Model):
            model.set_selected(True, update_checkbox=True)

    async def action_models_select_clear(self):
        for model in self.query(Model):
            model.set_selected(False, update_checkbox=True)

    async def action_models_find_next(self) -> None:
        """
        Action to compute the next stable model
        """
        try:
            next_model = await anext(self._model_generator)
        except StopAsyncIteration:
            return
        self._register_computed_model(next_model)

    async def action_models_find_all(self) -> None:
        """
        Action to compute all remaining stable models
        """
        async for model in aiter(self._model_generator):
            self._register_computed_model(model)

    def _register_computed_model(self, model: StableModel):
        self._models.add(model)
        models_widget = self.query_one(Models)
        models_widget.models = models_widget.models + 1

    def get_computed_models(self) -> Iterable[StableModel]:
        return self._models

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        """
        Check if any action may run
        """
        if action in self.actions:
            return self.actions[action].active
        else:
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


class Models(Static):

    models = reactive(1, recompose=True)

    def __init__(self, app: ClingexplaidTextualApp):
        super().__init__()
        self.app_handle = app

    def compose(self) -> ComposeResult:
        yield VerticalScroll(
            *sorted(
                [Model(model) for model in self.app_handle.get_computed_models()],
                key=lambda model: -model.get_model_id(),
            ),
        )
