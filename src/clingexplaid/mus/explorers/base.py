"""Abstract base class for all Explorers"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Generator, Iterable, List, Set

from ..utils import AssumptionWrapper


class ExplorationStatus(Enum):
    """Status of an assumption subset in an ongoing exploration process"""

    SATISFIABLE = 1
    UNSATISFIABLE = 2
    UNKNOWN = 3


class Explorer(ABC):
    """Abstract base class for all oracles"""

    def __init__(self, assumptions: Iterable[AssumptionWrapper]) -> None:
        self._assumptions = set(assumptions)
        self._found_sat: List[Set[AssumptionWrapper]] = []
        self._found_mus: List[Set[AssumptionWrapper]] = []

    @property
    def assumptions(self) -> Set[AssumptionWrapper]:  # nocoverage
        """All assumptions that the oracle can choose from"""
        return self._assumptions

    @property
    def mus_count(self) -> int:  # nocoverage
        """Number of MUS that have been found with the explorer"""
        return len(self._found_mus)

    def add_sat(self, assumptions: Iterable[AssumptionWrapper]) -> None:
        """Adds a satisfiable assumption set"""
        self._found_sat.append(set(assumptions))

    def add_mus(self, assumptions: Iterable[AssumptionWrapper]) -> None:
        """Adds a mus"""
        self._found_mus.append(set(assumptions))

    def reset(self) -> None:
        """Resets the found assumption sets"""
        self._found_sat.clear()
        self._found_mus.clear()

    @abstractmethod
    def explored(self, assumption_set: Set[AssumptionWrapper]) -> ExplorationStatus:
        """Returns the exploration status of a set of assumptions"""

    @abstractmethod
    def candidates(self) -> Generator[Set[AssumptionWrapper], None, None]:
        """Generator that produces the assumption set candidates"""
