"""
Custom types for clingexplaid
"""

from collections.abc import Iterable

import clingo

SymbolSet = set[clingo.Symbol]
Literal = tuple[clingo.Symbol, bool]
LiteralSet = set[Literal]
Assumption = Literal | int
AssumptionSet = Iterable[Assumption]
