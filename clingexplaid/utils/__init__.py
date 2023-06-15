from dataclasses import dataclass
from clingo.ast import ASTType
from typing import Tuple


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