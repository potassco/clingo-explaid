"""Explorers using the brute-force powerset approach"""

from itertools import chain, combinations
from typing import Generator, Iterable, List, Set

from ..utils import AssumptionWrapper
from .base import ExplorationStatus, Explorer


class ExplorerPowerset(Explorer):
    """Oracle using the brute-force powerset approach"""

    def __init__(self, assumptions: Iterable[AssumptionWrapper]) -> None:
        super().__init__(assumptions=assumptions)
        self._found_sat: List[Set[AssumptionWrapper]] = []
        self._found_mus: List[Set[AssumptionWrapper]] = []
        self._powerset = chain.from_iterable(
            combinations(assumptions, r) for r in reversed(range(len(list(assumptions)) + 1))
        )

    def reset(self) -> None:
        self._found_sat = []
        self._found_mus = []

    @property
    def mus_count(self) -> int:
        return len(self._found_mus)

    def add_mus(self, assumptions: Iterable[AssumptionWrapper]) -> None:
        self._found_mus.append(set(assumptions))

    def add_sat(self, assumptions: Iterable[AssumptionWrapper]) -> None:
        self._found_sat.append(set(assumptions))

    def candidates(self) -> Generator[Set[AssumptionWrapper], None, None]:
        for current_subset in (set(s) for s in self._powerset):
            # skip if empty subset
            if len(current_subset) == 0:
                continue
            # skip if an already found satisfiable subset is superset
            if any(set(sat).issuperset(current_subset) for sat in self._found_sat):
                continue
            # skip if an already found mus is a subset
            if any(set(mus).issubset(current_subset) for mus in self._found_mus):
                continue
            yield current_subset

    def explored(self, assumption_set: Set[AssumptionWrapper]) -> ExplorationStatus:
        if any(assumption_set.issubset(s) for s in self._found_sat):  # nocoverage
            return ExplorationStatus.SATISFIABLE
        if any(assumption_set.issuperset(s) for s in self._found_mus):  # nocoverage
            return ExplorationStatus.UNSATISFIABLE
        return ExplorationStatus.UNKNOWN
