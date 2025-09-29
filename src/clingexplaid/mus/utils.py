from dataclasses import dataclass
from typing import Iterable, Set

from clingo import Symbol


@dataclass
class AssumptionWrapper:
    """Container class for assumptions"""

    literal: int
    symbol: Symbol
    sign: bool

    def __hash__(self) -> int:
        return self.literal


def unwrap(wrapped: Iterable[AssumptionWrapper]) -> Set[int]:
    return {a.literal for a in wrapped}
