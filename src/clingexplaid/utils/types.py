"""
Custom types for clingexplaid
"""

from collections.abc import Iterable

import clingo

SymbolSetDEPRECATED = set[clingo.Symbol]
LiteralDEPRECATED = tuple[clingo.Symbol, bool]
LiteralSetDEPRECATED = set[LiteralDEPRECATED]
AssumptionDEPRECATED = LiteralDEPRECATED | int
AssumptionSetDEPRECATED = Iterable[AssumptionDEPRECATED]
