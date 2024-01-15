"""
Utilities
"""

import re
from typing import Dict, Iterable, Set, Tuple, Union

import clingo
from clingo.ast import ASTType

SymbolSet = Set[clingo.Symbol]
Literal = Tuple[clingo.Symbol, bool]
LiteralSet = Set[Literal]
Assumption = Union[Literal, int]
AssumptionSet = Iterable[Assumption]


def match_ast_symbolic_atom_signature(
    ast_symbol: ASTType.SymbolicAtom, signature: Tuple[str, int]
):
    """
    Function to match the signature of an AST SymbolicAtom to a tuple containing a string and int value, representing a
    matching signature.
    """

    symbol = str(ast_symbol.symbol)
    name = symbol.split("(", maxsplit=1)[0]
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


def get_signatures_from_model_string(model_string: str) -> Dict[str, int]:
    """
    This function returns a dictionary of the signatures/arities of all atoms of a model string. Model strings are of
    the form: `"signature1(X1, ..., XN) ... signatureM(X1, ..., XK)"`
    """
    signatures = {}
    for atom_string in model_string.split():
        result = re.search(r"([^(]*)\(", atom_string)
        if len(result.groups()) == 0:
            continue
        signature = result.group(1)
        # calculate arity for the signature
        arity = 0
        level = 0
        for c in atom_string.removeprefix(signature):
            if c == "(":
                level += 1
            elif c == ")":
                level -= 1
            else:
                if level == 1 and c == ",":
                    arity += 1
        # if arity is not 0 increase by 1 for the last remaining parameter that is not followed by a comma
        if arity > 0:
            arity += 1
        signatures[signature] = arity
    return signatures
