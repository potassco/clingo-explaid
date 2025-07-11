"""Collection of oracles for getting MUS candidates"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from itertools import chain, combinations
from typing import Dict, Generator, Iterable, List, Optional, Set

import clingo

from clingexplaid.utils.types import Assumption

ASSUMPTION_SYMBOL_NAME = "a"


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


@dataclass(frozen=True)
class RepresentationID:
    """ID for internal assumption representations of ExplorerASP"""

    id: int

    def __int__(self) -> int:
        return self.id


@dataclass(frozen=True)
class LiteralID:
    """ID for internal literal representations of ExplorerASP"""

    id: int

    def __int__(self) -> int:
        return self.id


class ExplorerAsp(Explorer):
    """Oracle using an ASP explore encoding for getting MUS candidates"""

    def __init__(self, assumptions: Iterable[Assumption]) -> None:
        super().__init__(assumptions=assumptions)
        self._control = clingo.Control(["--heuristic=Domain"])
        self._control.configuration.solve.models = 0  # type: ignore

        self._assumption_counter = 0
        self._assumption_to_rid: Dict[Assumption, RepresentationID] = {}
        self._rid_to_assumption: Dict[RepresentationID, Assumption] = {}

        self._rid_to_lid: Dict[RepresentationID, LiteralID] = {}
        self._lid_to_rid: Dict[LiteralID, RepresentationID] = {}

        # Add assumptions to control
        for assumption in self._assumptions:
            self._add_assumption(assumption)

    def _register_assumption_representation(self, assumption: Assumption) -> RepresentationID:
        self._assumption_counter += 1
        representation_id = RepresentationID(self._assumption_counter)
        self._rid_to_assumption[representation_id] = assumption
        self._assumption_to_rid[assumption] = representation_id
        return representation_id

    def _compose_assumption_atom(self, assumption: Assumption) -> clingo.Symbol:
        representation_id = self._assumption_to_rid[assumption]
        return clingo.Function(ASSUMPTION_SYMBOL_NAME, [clingo.Number(representation_id.id)])

    def _register_assumption_atom(self, assumption: Assumption, clingo_backend: clingo.Backend) -> LiteralID:
        assumption_symbol = self._compose_assumption_atom(assumption)
        literal_id = LiteralID(clingo_backend.add_atom(assumption_symbol))
        return literal_id

    def _add_assumption(self, assumption: Assumption) -> None:
        """Adds an assumption to the class control"""
        representation_id = self._register_assumption_representation(assumption)
        with self._control.backend() as backend:
            literal_id = self._register_assumption_atom(assumption, backend)
            # Store in lookup
            self._rid_to_lid[representation_id] = literal_id
            self._lid_to_rid[literal_id] = representation_id
            # Add choice and heuristic
            backend.add_heuristic(int(literal_id), clingo.backend.HeuristicType.True_, 1, 1, [])
            backend.add_rule([int(literal_id)], choice=True)

    def add_sat(self, assumptions: Iterable[Assumption]) -> None:
        super().add_sat(assumptions)
        # take difference of subset with all assumptions
        rule_assumptions = [a for a in self.assumptions if a not in assumptions]
        rule_literal_ids = [int(self._rid_to_lid[self._assumption_to_rid[a]]) for a in rule_assumptions]
        # invert difference assumptions
        rule_body = [-lid for lid in rule_literal_ids]
        with self._control.backend() as backend:
            backend.add_rule([], rule_body)

    def add_mus(self, assumptions: Iterable[Assumption]) -> None:
        super().add_mus(assumptions)
        rule_body = [int(self._rid_to_lid[self._assumption_to_rid[a]]) for a in assumptions]
        with self._control.backend() as backend:
            backend.add_rule([], rule_body)

    def _get_model(self) -> Optional[Set[clingo.Symbol]]:
        with self._control.solve(yield_=True) as solve_handle:
            if solve_handle.get().satisfiable:
                return set(solve_handle.model().symbols(atoms=True))
        return None

    def candidates(self) -> Generator[Set[Assumption], None, None]:
        while True:
            model = self._get_model()
            if model is None:
                break
            rids = [RepresentationID(int(str(atom.arguments[0]))) for atom in model]
            yield {self._rid_to_assumption[rid] for rid in rids}


class ExplorerType(Enum):
    """Types of explorers"""

    EXPLORER_POWERSET = 1
    EXPLORER_ASP = 2
