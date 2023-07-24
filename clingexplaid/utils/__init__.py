"""
Utilities
"""

from typing import Tuple, Dict, Set, Union
from collections.abc import Iterable

import clingo
from clingo.ast import ASTType


SymbolSet = Set[clingo.Symbol]
Literal = Tuple[clingo.Symbol, bool]
LiteralSet = Set[Literal]
Assumption = Union[Literal, int]
AssumptionSet = Iterable[Assumption]


def match_ast_symbolic_atom_signature(ast_symbol: ASTType.SymbolicAtom, signature: Tuple[str, int]):
    """
    Function to match the signature of an AST SymbolicAtom to a tuple containing a string and int value, representing a
    matching signature.
    """

    symbol = str(ast_symbol.symbol)
    name = symbol.split('(', maxsplit=1)[0]
    arity = len(ast_symbol.symbol.arguments)

    return all((signature[0] == name, signature[1] == arity))


def get_solver_literal_lookup(control: clingo.Control) -> Dict[int, clingo.Symbol]:
    """
    This function can be used to get a lookup dictionary to associate literal ids with their respective symbols for all
    symbolic atoms of the program
    """
    lookup = {}
    for atom in control.symbolic_atoms:
        lookup[atom.literal] = atom.symbol
    return lookup


__all__ = [
    match_ast_symbolic_atom_signature.__name__,
    get_solver_literal_lookup.__name__,
]
