"""Utility functions for handling clingo symbols."""

import clingo
from clingo.ast import AST


def ast_symbolic_atom_to_symbol(
    symbolic_atom: AST,
) -> clingo.Symbol:
    """Convert `SymbolicAtom`s of the clingo AST to clingo Symbols."""
    # TODO: this isn't an exactly nice conversion, should probably be changed in the future  # pylint: disable=fixme
    return clingo.parse_term(str(symbolic_atom))
