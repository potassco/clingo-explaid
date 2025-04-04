"""Utility functions for handling clingo symbols"""

import clingo
from clingo import ast


def ast_symbolic_atom_to_symbol(symbolic_atom: ast.ASTType.SymbolicAtom) -> clingo.Symbol:
    """Converts SymbolicAtoms of the clingo AST to clingo Symbols"""
    # TODO: this isn't an exactly nice conversion, should probably be changed in the future  # pylint: disable=fixme
    return clingo.parse_term(str(symbolic_atom))
