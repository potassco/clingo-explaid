from typing import Iterable

from textual.widgets import Log, Static

from .base import AbstractMode


class ExplanationMode(Static, AbstractMode):

    mode_css = ""
    mode_name = "Explanation"
    mode_id = "explanation"
    order = 3

    def __init__(self, files: Iterable[str], log: Log):
        super().__init__()
