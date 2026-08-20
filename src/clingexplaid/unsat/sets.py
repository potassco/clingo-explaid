"""
Container classes for sets
"""

from abc import ABC
from collections.abc import Iterator
from dataclasses import dataclass

import clingo

from .utils import AssumptionWrapper


def render_assumption(assumption: AssumptionWrapper) -> str:  # nocoverage
    assumption_sign = "+" if assumption.sign else "-"
    return f"{assumption.symbol}[{assumption.literal},{assumption_sign}]"


def render_assumption_set(assumptions: set[AssumptionWrapper]) -> str:  # nocoverage
    out = "{ "
    out += ", ".join([render_assumption(a) for a in assumptions])
    out += " }"
    return out


@dataclass(frozen=True)
class Subset(ABC):
    """Container class for different types for subsets"""

    assumptions: set[AssumptionWrapper]

    def iter_symbols(self) -> Iterator[tuple[clingo.Symbol, bool]]:
        """Iterate over all assumption symbols in the unsatisfiable subset"""
        return ((a.symbol, a.sign) for a in self.assumptions)

    def iter_literals(self) -> Iterator[int]:  # nocoverage
        """Iterate over all assumption literals in the unsatisfiable subset"""
        return (a.literal for a in self.assumptions)

    def __iter__(self) -> Iterator[tuple[clingo.Symbol, bool] | int]:
        return self.iter_symbols()

    @property
    def assumptions_string(self) -> str:  # nocoverage
        out = "assumptions="
        out += render_assumption_set(self.assumptions)
        return out

    @property
    def symbol_strings(self) -> set[str]:
        return {str(sym) for (sym, _) in self.iter_symbols()}

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.assumptions_string})"

    __repr__ = __str__


class SatisfiableSubset(Subset): ...


class UnsatisfiableSubset(Subset): ...


class MinimalUnsatisfiableSubset(Subset): ...


class MaximalSatisfiableSubset(Subset): ...


class MinimalCorrectionSet(Subset): ...
