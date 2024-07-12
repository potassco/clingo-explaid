from abc import ABC, ABCMeta, abstractmethod

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Collapsible, Label, Static


class ModeABCMeta(ABCMeta, type(Static)):
    pass


class AbstractMode(ABC, metaclass=ModeABCMeta):

    @abstractmethod
    def compose(self) -> ComposeResult:
        pass

    @property
    @abstractmethod
    def mode_name(self) -> str:
        pass

    @property
    @abstractmethod
    def mode_id(self) -> str:
        pass

    @property
    @abstractmethod
    def order(self) -> int:
        pass


class SolvingMode(Static, AbstractMode):

    mode_name = "Solving"
    mode_id = "solving"
    order = 1

    def compose(self) -> ComposeResult:
        yield VerticalScroll(Collapsible(Label("Some model information"), title="Model 1"))


class MinimalUnsatisfiableSubsetMode(Static, AbstractMode):

    mode_name = "Minimal Unsatisfiable Subsets"
    mode_id = "mus"
    order = 1

    def compose(self) -> ComposeResult:
        yield VerticalScroll(Collapsible(Label("Some MUS information"), title="MUS 1"))


class UnsatisfiableConstraintsMode(Static, AbstractMode):

    mode_name = "Unsatisfiable Constraints"
    mode_id = "unsat_constraints"
    order = 2

    def compose(self) -> ComposeResult:
        yield VerticalScroll(Collapsible(Label("Some unsat constraint information"), title="UNSAT CONSTRAINT 1"))
