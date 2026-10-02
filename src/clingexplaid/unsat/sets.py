"""Container classes for sets."""

from abc import ABC
from collections.abc import Iterator
from dataclasses import dataclass

import clingo

from .utils import AssumptionWrapper


def render_assumption(assumption: AssumptionWrapper) -> str:  # nocoverage
    """
    Render `assumption` in text format.

    Parameters
    ----------
    assumption
        The assumption to be rendered.

    Returns
    -------
        The rendered assumption string.
    """
    assumption_sign = "+" if assumption.sign else "-"
    return f"{assumption.symbol}[{assumption.literal},{assumption_sign}]"


def render_assumption_set(assumptions: set[AssumptionWrapper]) -> str:  # nocoverage
    """
    Render `assumptions` in text format.

    Parameters
    ----------
    assumptions
        A set of assumption to be rendered.

    Returns
    -------
        The rendered assumptions string.
    """
    out = "{ "
    out += ", ".join([render_assumption(a) for a in assumptions])
    out += " }"
    return out


@dataclass(frozen=True)
class Subset(ABC):
    """Container class for different types for subsets."""

    assumptions: set[AssumptionWrapper]

    def iter_symbols(self) -> Iterator[tuple[clingo.Symbol, bool]]:
        """Iterate over all assumption symbols in the unsatisfiable subset."""
        return ((a.symbol, a.sign) for a in self.assumptions)

    def iter_literals(self) -> Iterator[int]:  # nocoverage
        """Iterate over all assumption literals in the unsatisfiable subset."""
        return (a.literal for a in self.assumptions)

    def __iter__(self) -> Iterator[tuple[clingo.Symbol, bool] | int]:
        """Iterate of the assumption symbols."""
        return self.iter_symbols()

    @property
    def assumptions_string(self) -> str:  # nocoverage
        """A rendered string representation of the assumptions."""
        out = "assumptions="
        out += render_assumption_set(self.assumptions)
        return out

    @property
    def symbol_strings(self) -> set[str]:
        """A set of rendered string representation of the assumption symbols."""
        return {str(sym) for (sym, _) in self.iter_symbols()}

    def __str__(self) -> str:
        """Return a string representation of the subset."""
        return f"{self.__class__.__name__}({self.assumptions_string})"

    __repr__ = __str__


class SatisfiableSubset(Subset):
    """Container class for satisfiable subsets."""


class UnsatisfiableSubset(Subset):
    """Container class for unsatisfiable subsets."""


class MinimalUnsatisfiableSubset(Subset):
    """Container class for minimal unsatisfiable subsets (MUS)."""


class MaximalSatisfiableSubset(Subset):
    """Container class for maximal satisfiable subsets (MSS)."""


class MinimalCorrectionSet(Subset):
    """Container class for minimal correction sets (MUS)."""
