import os
from pathlib import Path
from typing import Iterable, List, Optional, cast

from rich.style import Style
from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, Log, Static, TextArea, Tree
from textual.widgets.tree import TreeNode

from ...explain import get_explanation_factbase
from ...explain.textual import textualize_clingraph_factbase
from ..style import MODE_EXPLANATION_STYLE
from .base import AbstractMode

REASON_STRING_LACK_OF_SUPPORT = "No rule can support"


class ExplanationMode(Static, AbstractMode):

    mode_css = MODE_EXPLANATION_STYLE
    mode_name = "Explanation"
    mode_id = "explanation"
    order = 3

    def __init__(self, files: Iterable[str], log: Log, answer_set: Optional[str] = None):
        super().__init__()
        self.files = files
        self.explanation_tree = Tree("Explanation Tree")
        self.tree_cursor: TreeNode = self.explanation_tree.root
        self.answer_set = answer_set
        self.answer_set_atoms = set() if answer_set is None else set([a.removesuffix(".") for a in answer_set.split()])
        self.logger = log

    def compose(self) -> ComposeResult:
        ta_answer_set = TextArea(id="answer_set")
        if self.answer_set is not None:
            ta_answer_set.text = self.answer_set
        ta_answer_set.border_title = "Answer Set"
        ta_query = TextArea(id="query_atom")
        ta_query.border_title = "Query"
        ta_false = TextArea(id="false_atoms")
        ta_false.border_title = "False Atoms"
        yield Horizontal(ta_answer_set, ta_query, ta_false, id="inputs")
        yield Button("🔍", classes="outlined", id="explain_button")
        yield self.explanation_tree

    @on(Button.Pressed)
    async def _button_pressed(self, event: Button.Pressed) -> None:
        if event.button == self.query_one("#explain_button"):
            self.query_one(Tree).focus()
            await self._explain()

    async def _explain(self):
        answer_set = cast(TextArea, self.query_one("#answer_set")).text
        query_atom = cast(TextArea, self.query_one("#query_atom")).text
        false_atoms = cast(TextArea, self.query_one("#false_atoms")).text
        cwd = Path(os.getcwd())
        files = []
        for file in self.files:
            files.append(str(cwd.joinpath(file).resolve()))
        fb = get_explanation_factbase(
            files=files,
            query=query_atom,
            answer_set=answer_set,
            false_atoms=false_atoms.split(),
        )
        nested, expand_depth = textualize_clingraph_factbase(fb, 2)  # TODO: removed fixed expand depth
        self._reset_tree()
        await self._build_nested_explanation_tree(self.tree_cursor, nested)

    async def _build_nested_explanation_tree(
        self, node: TreeNode, nested_list: List, level: int = 0, auto_expand_level: int = 2
    ) -> None:
        new_node = None
        for elem in nested_list:
            if isinstance(elem, list):
                await self._build_nested_explanation_tree(
                    new_node, elem, level + 1, auto_expand_level=auto_expand_level
                )
            else:
                if elem.name == "root":
                    # skip root node
                    new_node = node
                else:
                    node_title = f" {elem.name} "
                    if elem.incoming_rule is not None:
                        node_title += f" ({elem.incoming_rule})"
                    new_node = node.add(node_title)
                    in_answer_set = elem.name in self.answer_set_atoms
                    new_node.label.stylize(
                        Style(bgcolor="#00FF00" if in_answer_set else "#FF0000"),
                        0,
                        len(elem.name) + 2,
                    )
                    new_node.label.stylize("#888888", len(elem.name) + 3)

                    if level <= auto_expand_level:
                        new_node.expand()
                    reason_string = str(elem.reason).replace('"', "")
                    is_lack_of_support = reason_string == REASON_STRING_LACK_OF_SUPPORT
                    rule_string = str(elem.rule).replace('"', "")
                    reason = new_node.add_leaf(f"Reason: {reason_string}")
                    reason.label.stylize("bold #0087D7", 0, 7)
                    if not is_lack_of_support:
                        rule = new_node.add_leaf(f"Rule: {rule_string}")
                        rule.label.stylize("bold #0087D7", 0, 5)
                        rule.label.stylize("#888888", 6)

    def _reset_tree(self):
        self.explanation_tree.reset(self.explanation_tree.root.label)
        self.tree_cursor = self.explanation_tree.root
        self.tree_cursor.expand()
