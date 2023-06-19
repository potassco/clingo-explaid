from dataclasses import dataclass

import clingo
from clingo.ast import ASTType
from typing import Tuple, List, Dict


def match_ast_symbolic_atom_signature(ast_symbol:ASTType.SymbolicAtom, signature: Tuple[str, int]):
    symbol = str(ast_symbol.symbol)
    name = symbol.split('(')[0]
    arity = 0

    depth = 0
    for c in symbol:
        if c == "(":
            if arity == 0:
                arity = 1
            depth += 1
        elif c == ")":
            depth -= 1

        if depth != 1:
            continue
        if c == ",":
            arity += 1

    return all((signature[0] == name, signature[1] == arity))


def get_solver_literal_lookup(control: clingo.Control) -> Dict[int, clingo.Symbol]:
    """
    This function can be used to get a lookup dictionary to associate literal ids with their respective symbols for all
    symbolic atoms of the program
    """
    lookup = dict()
    for atom in control.symbolic_atoms:
        lookup[atom.literal] = atom.symbol
    return lookup
