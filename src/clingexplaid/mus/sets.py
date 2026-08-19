from collections.abc import Iterator
from dataclasses import dataclass

import clingo

from .utils import AssumptionWrapper


@dataclass(frozen=True)
class UnsatisfiableSubset:
    """Container class for unsatisfiable subsets"""

    assumptions: set[AssumptionWrapper]
    minimal: bool = False

    @staticmethod
    def _render_assumption(assumption: AssumptionWrapper) -> str:  # nocoverage
        assumption_sign = "+" if assumption.sign else "-"
        return f"{assumption.symbol}[{assumption.literal},{assumption_sign}]"

    @staticmethod
    def _render_assumption_set(
        assumptions: set[AssumptionWrapper],
    ) -> str:  # nocoverage
        out = "{"
        out += ",".join([UnsatisfiableSubset._render_assumption(a) for a in assumptions])
        out += "}"
        return out

    def iter_symbols(self) -> Iterator[tuple[clingo.Symbol, bool]]:
        """Iterate over all assumption symbols in the unsatisfiable subset"""
        return ((a.symbol, a.sign) for a in self.assumptions)

    def iter_literals(self) -> Iterator[tuple[int, bool]]:  # nocoverage
        """Iterate over all assumption literals in the unsatisfiable subset"""
        return ((a.literal, a.sign) for a in self.assumptions)

    def __iter__(self) -> Iterator[tuple[clingo.Symbol, bool] | int]:
        return self.iter_symbols()

    def __str__(self) -> str:  # nocoverage
        out = "UnsatisfiableSubset("
        out += "assumptions="
        out += UnsatisfiableSubset._render_assumption_set(self.assumptions)
        out += ", minimal="
        out += str(self.minimal)
        out += ")"
        return out

    __repr__ = __str__
