from typing import Iterable

from textual.widgets import Log, Static

from .base import AbstractMode


class SolverDecisionsMode(Static, AbstractMode):

    mode_name = "Solver Decisions"
    mode_id = "solver_decisions"
    order = 2

    def __init__(self, files: Iterable[str], log: Log):
        super().__init__()
