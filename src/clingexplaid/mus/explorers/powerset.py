from itertools import chain, combinations
from typing import Generator, Iterable, Set

from ..utils import AssumptionWrapper
from .base import ExplorationStatus, Explorer


class ExplorerPowerset(Explorer):
    """Oracle using the brute-force powerset approach"""

    def __init__(self, assumptions: Iterable[AssumptionWrapper]) -> None:
        super().__init__(assumptions=assumptions)
        self._powerset = chain.from_iterable(
            combinations(assumptions, r) for r in reversed(range(len(list(assumptions)) + 1))
        )

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
        if any(assumption_set.issubset(s) for s in self._found_sat):
            return ExplorationStatus.SATISFIABLE
        if any(assumption_set.issuperset(s) for s in self._found_mus):
            return ExplorationStatus.SATISFIABLE
        return ExplorationStatus.UNKNOWN
