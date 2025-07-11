"""Collection of oracles for getting MUS candidates"""

from abc import ABC, abstractmethod
from enum import Enum
from itertools import chain, combinations
from typing import Generator, Iterable, List, Set

from clingexplaid.utils.types import Assumption


class Explorer(ABC):
    """Abstract base class for all oracles"""

    def __init__(self, assumptions: Iterable[Assumption]) -> None:
        self._assumptions = set(assumptions)
        self._found_sat: List[Set[Assumption]] = []
        self._found_mus: List[Set[Assumption]] = []

    @property
    def assumptions(self) -> Set[Assumption]:  # nocoverage
        """All assumptions that the oracle can choose from"""
        return self._assumptions

    @property
    def found_sat(self) -> List[Set[Assumption]]:  # nocoverage
        """Set of all found satisfiable assumption sets"""
        return self._found_sat

    @property
    def found_mus(self) -> List[Set[Assumption]]:  # nocoverage
        """Set of all found mus"""
        return self._found_mus

    def add_sat(self, assumptions: Iterable[Assumption]) -> None:
        """Adds a satisfiable assumption set"""
        self._found_sat.append(set(assumptions))

    def add_mus(self, assumptions: Iterable[Assumption]) -> None:
        """Adds a mus"""
        self._found_mus.append(set(assumptions))

    def reset(self) -> None:
        """Resets the found assumption sets"""
        self._found_sat.clear()
        self._found_mus.clear()

    @abstractmethod
    def candidates(self) -> Generator[Set[Assumption], None, None]:
        """Generator that produces the assumption set candidates"""


class ExplorerPowerset(Explorer):
    """Oracle using the brute-force powerset approach"""

    def __init__(self, assumptions: Iterable[Assumption]) -> None:
        super().__init__(assumptions=assumptions)
        self._powerset = chain.from_iterable(
            combinations(assumptions, r) for r in reversed(range(len(list(assumptions)) + 1))
        )

    def candidates(self) -> Generator[Set[Assumption], None, None]:
        for current_subset in (set(s) for s in self._powerset):
            # skip if empty subset
            if len(current_subset) == 0:
                continue
            # skip if an already found satisfiable subset is superset
            if any(set(sat).issuperset(current_subset) for sat in self.found_sat):
                continue
            # skip if an already found mus is a subset
            if any(set(mus).issubset(current_subset) for mus in self.found_mus):
                continue
            yield current_subset


class ExplorerAsp(Explorer):
    """Oracle using an ASP explore encoding for getting MUS candidates"""

    def candidates(self) -> Generator[Set[Assumption], None, None]:
        raise NotImplementedError("The ASP Explorer Oracle is not yet implemented")  # nocoverage


class ExplorerType(Enum):
    """Types of explorers"""

    EXPLORER_POWERSET = 1
    EXPLORER_ASP = 2
