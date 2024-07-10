from dataclasses import dataclass
from typing import List, Optional, Tuple

import clingo
import clorm.orm.core
from clingraph.orm import Factbase
from rich.style import Style
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Tree
from textual.widgets.tree import TreeNode

REASON_STRING_LACK_OF_SUPPORT = "No rule can support"
COLOR_MAP = {"#609E60": "#2E7D32", "#F6B0B0": "#D32F2F"}


def split_tuple_string(string: str) -> Tuple[str, str]:
    level = 0
    left = []
    right = []
    current = left
    for char in string:
        if level == 1 and char == ",":
            current = right
            continue
        if char == "(":
            level += 1
            if level == 1:
                continue
        if char == ")":
            level -= 1
            if level == 0:
                continue
        current.append(char)
    return "".join(left), "".join(right)


@dataclass
class TextNode:
    name: str
    reason: str
    rule: str
    color: str
    incoming_rule: Optional[str] = None


def expand_node(
    node: str,
    edges,
    associated_reasons,
    associated_rules,
    incoming_rules,
    node_colors,
    has_incoming_rule=False,
):
    reason = associated_reasons.get(node)
    rule = associated_rules.get(node)
    color = str(node_colors.get(node)).replace('"', "")
    if color in COLOR_MAP:
        color = COLOR_MAP[color]
    node_object = TextNode(
        name=node,
        reason=reason,
        rule=rule,
        color=color,
    )
    has_incoming = str(reason).replace('"', "") == REASON_STRING_LACK_OF_SUPPORT
    if has_incoming_rule:
        node_object.incoming_rule = str(incoming_rules.get(node)).replace('"', "")
    if node in edges:
        return [
            node_object,
            *[
                expand_node(
                    edge,
                    edges,
                    associated_reasons,
                    associated_rules,
                    incoming_rules,
                    node_colors,
                    has_incoming_rule=has_incoming,
                )
                for edge in edges[node]
            ],
        ]
    return [node_object]


def print_nested(nested_list, level=0):
    for elem in nested_list:
        if isinstance(elem, list):
            print_nested(elem, level + 1)
        else:
            print(level * "-" + str(elem))


def textualize_clingraph_factbase(factbase: Factbase, expand_depth: int) -> Tuple[List[TextNode], int]:
    clorm_fb = factbase.fb
    fb_nodes = list(clorm_fb.query(factbase.Node).all())
    fb_edges = list(clorm_fb.query(factbase.Edge).all())
    print("-" * 50)
    print(fb_nodes)
    edges = {}
    node_lookup = {}
    for n in fb_nodes:
        node, parent = split_tuple_string(str(n.id))
        node_lookup[str(n.id)] = node
        if parent in edges:
            edges[parent].add(node_lookup[str(n.id)])
        else:
            edges[parent] = {node_lookup[str(n.id)]}
    # this step is redundant if each node has only one incoming edge
    for e in fb_edges:
        n1, n2 = split_tuple_string(str(e.id))
        parent = node_lookup[n1]
        node = node_lookup[n2]
        if parent in edges:
            edges[parent].add(node)
        else:
            edges[parent] = {node}
    # -----
    reasons = (
        clorm_fb.query(factbase.Attr)
        .where(
            factbase.Attr.element_type == "node",
            factbase.Attr.attr_id[0] == "label",
            factbase.Attr.attr_id[1] == clorm.orm.core.Raw(clingo.parse_term("reason")),
        )
        .select(factbase.Attr.element_id, factbase.Attr.attr_value)
        .all()
    )
    rules = (
        clorm_fb.query(factbase.Attr)
        .where(
            factbase.Attr.element_type == "node",
            factbase.Attr.attr_id[0] == "label",
            factbase.Attr.attr_id[1] == clorm.orm.core.Raw(clingo.parse_term("rule")),
        )
        .select(factbase.Attr.element_id, factbase.Attr.attr_value)
        .all()
    )
    edge_rules = (
        clorm_fb.query(factbase.Attr)
        .where(
            factbase.Attr.element_type == "edge",
            factbase.Attr.attr_id[0] == "label",
            factbase.Attr.attr_id[1] == clorm.orm.core.Raw(clingo.parse_term("rule")),
        )
        .select(factbase.Attr.element_id, factbase.Attr.attr_value)
        .all()
    )
    incoming_rules = {
        split_tuple_string(split_tuple_string(str(edge))[1])[0]: incoming_rule for edge, incoming_rule in edge_rules
    }
    node_color = (
        clorm_fb.query(factbase.Attr)
        .where(
            factbase.Attr.element_type == "node",
            factbase.Attr.attr_id[0] == "fillcolor",
        )
        .select(factbase.Attr.element_id, factbase.Attr.attr_value)
        .all()
    )
    node_colors = {node_lookup[str(node)]: color for node, color in node_color}
    reasons = {node_lookup[str(node)]: reason for node, reason in reasons}
    rules = {node_lookup[str(node)]: rule for node, rule in rules}
    # -----
    nested = expand_node("root", edges, reasons, rules, incoming_rules, node_colors)

    return nested, expand_depth


class TextTreeApp(App):
    """A textual app to show the explanation forrest in an interactive tree view in the terminal"""

    BINDINGS = [("d", "toggle_dark", "Toggle dark mode"), ("x", "exit", "Exit")]

    def __init__(self, data: List, expand_depth: int):
        super(TextTreeApp, self).__init__()
        self.data = data
        self.expand_depth = expand_depth

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        t = Tree("Explanation Tree", id="explanation-tree")
        self.build_tree(t.root, self.data, auto_expand_level=self.expand_depth)
        t.root.expand()
        yield t

    @staticmethod
    def build_tree(node: TreeNode, nested_list: List, level: int = 0, auto_expand_level: int = 2) -> None:
        new_node = None
        for elem in nested_list:
            if isinstance(elem, list):
                TextTreeApp.build_tree(new_node, elem, level + 1, auto_expand_level=auto_expand_level)
            else:
                if elem.name == "root":
                    # skip root node
                    new_node = node
                else:
                    node_title = f" {elem.name} "
                    if elem.incoming_rule is not None:
                        node_title += f" ({elem.incoming_rule})"
                    new_node = node.add(node_title)
                    new_node.label.stylize(
                        Style(bgcolor=str(elem.color)),
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

    def action_exit(self):
        self.exit()

    def action_add(self):
        tree = self.query_one(Tree)
        tree.root.add("TEST")

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark
