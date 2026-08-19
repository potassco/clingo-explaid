"""
Container classes for sets
"""

from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum

import clingo

from .utils import AssumptionWrapper


def render_assumption(assumption: AssumptionWrapper) -> str:  # nocoverage
    assumption_sign = "+" if assumption.sign else "-"
    return f"{assumption.symbol}[{assumption.literal},{assumption_sign}]"


def render_assumption_set(assumptions: set[AssumptionWrapper]) -> str:  # nocoverage
    out = "{"
    out += ",".join([render_assumption(a) for a in assumptions])
    out += "}"
    return out


class SubsetType(Enum):
    UnsatisfiableSubset = "US"
    SatisfiableSubset = "SS"
    MinimalUnsatisfiableSubset = "MUS"
    MaximalSatisfiableSubset = "MSS"
    MinimalCorrectionSet = "MCS"


@dataclass(frozen=True)
class Subset:
    """Container class for different types for subsets"""

    type: SubsetType
    assumptions: set[AssumptionWrapper]

    def iter_symbols(self) -> Iterator[tuple[clingo.Symbol, bool]]:
        """Iterate over all assumption symbols in the unsatisfiable subset"""
        return ((a.symbol, a.sign) for a in self.assumptions)

    def iter_literals(self) -> Iterator[int]:  # nocoverage
        """Iterate over all assumption literals in the unsatisfiable subset"""
        return (a.literal for a in self.assumptions)

    def __iter__(self) -> Iterator[tuple[clingo.Symbol, bool] | int]:
        return self.iter_symbols()

    def __str__(self) -> str:  # nocoverage
        out = f"{self.type.name}("
        out += "assumptions="
        out += render_assumption_set(self.assumptions)
        out += ")"
        return out

    __repr__ = __str__
