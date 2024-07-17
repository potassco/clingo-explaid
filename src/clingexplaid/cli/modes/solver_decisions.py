from typing import Iterable, List, Union, cast

import clingo
from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.widgets import Button, Log, Static, Tree
from textual.widgets.tree import TreeNode

from ...propagators import SolverDecisionPropagator
from ...propagators.propagator_solver_decisions import Decision
from ..style import MODE_SOLVER_DECISIONS_STYLE
from .base import AbstractMode


class SolverDecisionsMode(Static, AbstractMode):

    mode_css = MODE_SOLVER_DECISIONS_STYLE
    mode_name = "Solver Decisions"
    mode_id = "solver_decisions"
    order = 2

    def __init__(self, files: Iterable[str], log: Log):
        super().__init__()
        self.files = files
        self.solver_tree: Tree = Tree(id="solver-tree", label=self.mode_name)
        self.tree_cursor: TreeNode = self.solver_tree.root
        self.logger = log

    def compose(self) -> ComposeResult:
        b = Button("⚙️ ", classes="outlined", id="compute_button")
        yield b
        yield self.solver_tree

    @on(Button.Pressed)
    async def _button_pressed(self, event: Button.Pressed):
        if event.button == self.query_one("#compute_button"):
            self.solver_tree.focus()
            await self._compute_solver_decisions()

    async def _compute_solver_decisions(self) -> None:
        self._reset_tree()

        control = clingo.Control()
        sdp = SolverDecisionPropagator(
            callback_propagate=self._on_propagate,
            callback_undo=self._on_undo,
        )
        control.register_propagator(sdp)
        for file in self.files:
            control.load(file)
        control.ground([("base", [])])

        control.configuration.solve.models = 0
        control.solve(on_model=self._on_model)

        self.logger.write("FINISHED")

    def _on_model(self, model: clingo.Model) -> None:
        self.tree_cursor.add_leaf(f"MODEL: {' '.join([str(a) for a in model.symbols(shown=True)])}")

    def _on_propagate(self, decisions: List[Union[Decision, List[Decision]]]) -> None:
        for element in decisions:
            if isinstance(element, list):
                for literal in element:
                    entailment = self.tree_cursor.add_leaf(str(literal)).expand()
                    cast(Text, entailment.label).stylize("#333333")
            else:
                new_node = self.tree_cursor.add(str(element))
                new_node.expand()
                self.tree_cursor = new_node

    def _on_undo(self) -> None:
        undo = self.tree_cursor.add_leaf(f"UNDO {self.tree_cursor.label}")
        cast(Text, undo.label).stylize("#FF0000")
        self.tree_cursor = self.tree_cursor.parent

    def _reset_tree(self):
        self.solver_tree.reset(self.solver_tree.root.label)
        self.tree_cursor = self.solver_tree.root
        self.tree_cursor.expand()
