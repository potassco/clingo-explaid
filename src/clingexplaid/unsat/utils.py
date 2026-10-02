"""Utilities for the MUS functionality of clingexplaid."""

from collections.abc import Iterable
from dataclasses import dataclass

from clingo import Symbol


@dataclass(frozen=True)
class AssumptionWrapper:
    """Container class for assumptions."""

    literal: int
    symbol: Symbol
    sign: bool

    def __hash__(self) -> int:
        """Return `self.literal` for hashing."""
        return self.literal


def unwrap(wrapped: Iterable[AssumptionWrapper]) -> set[int]:
    """Unwrap an iterable sequence of assumptions into its set of literals."""
    return {a.literal for a in wrapped}
