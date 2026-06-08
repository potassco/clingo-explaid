"""
Transformer Module: Removing all optimization statements
"""

from collections.abc import Sequence
from pathlib import Path

from clingo.ast import AST, Function, Rule, Transformer, parse_files, parse_string

from .constants import REMOVED_TOKEN


class OptimizationRemover(Transformer):
    """
    Transformer that removes all optimization statements
    """

    # pylint: disable=duplicate-code

    def visit_Minimize(self, node: AST) -> AST:  # pylint: disable=C0103
        """
        Removes all facts from a program that match the given signatures (if none are given all facts are removed).
        """
        return Rule(
            location=node.location,
            head=Function(location=node.location, name=REMOVED_TOKEN, arguments=[], external=0),
            body=[],
        )

    @staticmethod
    def post_transform(program_string: str) -> str:
        """
        Helper function that is called after the transformation process for cleanup purposes
        """
        # remove the transformed REMOVED_TOKENS from the resulting program string
        rules = program_string.split("\n")
        out: list[str] = []
        for rule in rules:
            if not rule.startswith(REMOVED_TOKEN):
                out.append(rule)
        return "\n".join(out)

    def parse_string(self, string: str) -> str:
        """
        Function that applies the transformation to the `program_string` it's called with and returns the transformed
        program string.
        """
        out: list[str] = []
        parse_string(string, lambda stm: out.append(str(self(stm))))
        return self.post_transform("\n".join(out))

    def parse_files(self, paths: Sequence[str | Path]) -> str:
        """
        Parses the files and returns a string with the transformed program.
        """
        out: list[str] = []
        parse_files(
            [str(p) for p in paths],
            lambda stm: out.append(str(self(stm))),
        )
        return self.post_transform("\n".join(out))
