"""Utilities for the MUS functionality of clingexplaid"""

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from enum import Enum
from typing import override

from clingo import Symbol


class SatisfiableSubsetType(Enum):
    UNKNOWN = "unknown"
    MAXIMAL = "maximal"
    NON_MAXIMAL = "non-maxmimal"


class UnsatisfiableSubsetType(Enum):
    UNKNOWN = "unknown"
    MINIMAL = "minimal"
    NON_MINIMAL = "non-minimal"


@dataclass
class AssumptionWrapper:
    """Container class for assumptions"""

    literal: int
    symbol: Symbol
    sign: bool

    def __hash__(self) -> int:
        return self.literal


@dataclass
class AssumptionSet:
    """Container class for assumption set"""

    assumptions: set[AssumptionWrapper]

    @staticmethod
    def _render_assumption(assumption: AssumptionWrapper) -> str:  # nocoverage
        assumption_sign = "+" if assumption.sign else "-"
        return f"{assumption.symbol}[{assumption.literal},{assumption_sign}]"

    @staticmethod
    def _render_assumption_set(
        assumptions: set[AssumptionWrapper],
    ) -> str:  # nocoverage
        out = "{"
        out += ",".join([AssumptionSet._render_assumption(a) for a in assumptions])
        out += "}"
        return out

    def iter_symbols(self) -> Iterator[tuple[Symbol, bool]]:
        """Iterate over all assumption symbols in the unsatisfiable subset"""
        return ((a.symbol, a.sign) for a in self.assumptions)

    def iter_literals(self) -> Iterator[tuple[int, bool]]:  # nocoverage
        """Iterate over all assumption literals in the unsatisfiable subset"""
        return ((a.literal, a.sign) for a in self.assumptions)

    def __iter__(self) -> Iterator[tuple[Symbol, bool] | int]:
        return self.iter_symbols()

    @override
    def __str__(self) -> str:  # nocoverage
        out = f"{self.__class__.__name__}("
        out += "assumptions="
        out += AssumptionSet._render_assumption_set(self.assumptions)
        out += ")"
        return out

    @override
    def __repr__(self) -> str:  # nocoverage
        return self.__str__()


@dataclass
class UnsatisfiableSubset(AssumptionSet):
    """Container class for unsatisfiable assumption subset"""

    type: UnsatisfiableSubsetType = UnsatisfiableSubsetType.UNKNOWN


@dataclass
class SatisfiableSubset(AssumptionSet):
    """Container class for satisfiable assumption subset"""

    type: SatisfiableSubsetType = SatisfiableSubsetType.UNKNOWN


def unwrap_assumptions(wrapped: Iterable[AssumptionWrapper]) -> set[int]:
    """Unwraps an iterable sequence of assumptions into its set of literals"""
    return {a.literal for a in wrapped}
