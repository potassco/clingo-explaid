from abc import ABC, ABCMeta, abstractmethod

from textual.app import ComposeResult
from textual.widgets import Static


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

    @property
    @abstractmethod
    def mode_css(self) -> str:
        pass
