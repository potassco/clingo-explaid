"""Transformer to remove facts for a program."""

from pathlib import Path
from typing import Optional, Sequence, Set, Tuple, Union

from clingo.ast import AST, ASTType, Function, Rule, Transformer, parse_files, parse_string

from ..utils import match_ast_symbolic_atom_signature
from .constants import REMOVED_TOKEN


class FactTransformer(Transformer):
    """Transformer removes all facts from a program that match provided signatures."""

    # pylint: disable=duplicate-code

    def __init__(self, signatures: Optional[Set[Tuple[str, int]]] = None) -> None:
        self.signatures = signatures if signatures is not None else set()

    def visit_Rule(self, node: AST) -> AST:  # pylint: disable=C0103
        """Remove all facts from a program that match the given signatures (if none are given all facts are removed)."""
        if node.head.ast_type != ASTType.Literal:
            return node
        if node.body:
            return node
        has_matching_signature = any(
            match_ast_symbolic_atom_signature(node.head.atom, (name, arity)) for (name, arity) in self.signatures
        )
        # if signatures are defined only transform facts that match them, else transform all facts
        if self.signatures and not has_matching_signature:
            return node

        return Rule(
            location=node.location,
            head=Function(location=node.location, name=REMOVED_TOKEN, arguments=[], external=0),
            body=[],
        )

    @staticmethod
    def post_transform(program_string: str) -> str:
        """Return a cleaned-up version after the transformation."""
        # remove the transformed REMOVED_TOKENS from the resulting program string
        rules = program_string.split("\n")
        out = []
        for rule in rules:
            if not rule.startswith(REMOVED_TOKEN):
                out.append(rule)
        return "\n".join(out)

    def parse_string(self, string: str) -> str:
        """Transform the provided string and return its transformation."""
        out = []
        parse_string(string, lambda stm: out.append(str(self(stm))))
        return self.post_transform("\n".join(out))

    def parse_files(self, paths: Sequence[Union[str, Path]]) -> str:
        """Transform the provided list of files and return a concatination of their transformations."""
        out = []
        parse_files(
            [str(p) for p in paths],
            lambda stm: out.append(str(self(stm))),
        )
        return self.post_transform("\n".join(out))
