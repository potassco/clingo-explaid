from typing import Generator, Iterable

import clingo
from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.reactive import reactive
from textual.widgets import Button, Collapsible, Log, Static

from ..util import Atom, StableModel
from .base import AbstractMode


class StableModelWidget(Static):

    def __init__(self, stable_model: StableModel, expanded: bool = False):
        super().__init__()
        self.model: StableModel = stable_model
        self.expanded = expanded

    def compose(self) -> ComposeResult:
        yield Collapsible(
            Collapsible(*self._get_model_atoms(), title="Atoms", collapsed=False),
            Horizontal(
                Static(),
                Button("Explain", id=f"explain-{self.model.model_id}"),
                Button("Compare"),
            ),
            collapsed=not self.expanded,
            classes="model",
            title=f"Model {self.model.model_id}",
        )

    def _get_model_atoms(self) -> ComposeResult:
        yield Static(" ".join([str(s.symbol) for s in self.model.atoms]))


class SolvingMode(Static, AbstractMode):

    mode_name = "Solving"
    mode_id = "solving"
    order = 1

    reactive_model_count = reactive(0, recompose=True)

    def __init__(self, files: Iterable[str], log: Log):
        super().__init__()
        self.files: Iterable[str] = files
        self.logger = log
        self.control: clingo.Control = clingo.Control("0")

        self.model_generator = self._get_models()
        self.exhausted: bool = False
        self.models = []

        for file in files:
            self.control.load(file)
        self.control.ground([("base", [])])
        self.models.append(next(self.model_generator))

    def compose(self) -> ComposeResult:
        button_classes = {"outlined"}
        if self.exhausted:
            button_classes.add("hidden")
        yield Button("➕", classes=" ".join(button_classes), id="next_model_button")
        yield VerticalScroll(*self._compose_stable_models())

    def _compose_stable_models(self):
        for i, model in enumerate(reversed(self.models)):
            auto_expanded = i == 0
            yield StableModelWidget(stable_model=model, expanded=auto_expanded)

    @on(Button.Pressed)
    async def _button_pressed(self, event: Button.Pressed) -> None:
        if event.button == self.query_one("#next_model_button"):
            if not self.exhausted:
                self.models.append(next(self.model_generator))
                self.logger.write(f"exhause: {self.exhausted}\n")
        elif event.button.id.startswith("explain-"):
            model_id = int(event.button.id.removeprefix("explain-"))
            self.logger.write(f"Used Model {model_id}\n")
            await self.run_action("app.switch_mode('explanation')")
            self.logger.write("Switched\n")
            self.logger.write("HERE THE TABS SHOULD ALSO BE UPDATED!\n")

    def _get_models(self) -> Generator[StableModel, None, None]:
        with self.control.solve(yield_=True) as solve_handle:
            if not solve_handle.get().satisfiable:
                # return if unsatisfiable
                return
            while True:
                result = solve_handle.get()
                if result.exhausted:
                    break
                model = solve_handle.model()
                atoms = set()
                shown = model.symbols(shown=True)
                for symbol in model.symbols(atoms=True):
                    atoms.add(Atom(0, 0, symbol, symbol in shown))
                output_model = StableModel(model_id=self._bump_model_count(), atoms=atoms)
                solve_handle.resume()
                if solve_handle.get().exhausted:
                    self.exhausted = True
                yield output_model

    def _bump_model_count(self) -> int:
        next_model_id = 1 if self.reactive_model_count == 0 else self.reactive_model_count + 1
        self.reactive_model_count = next_model_id
        return next_model_id
