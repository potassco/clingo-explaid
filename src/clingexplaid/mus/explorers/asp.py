"""Explorer using ASP for getting MUS candidates"""

from dataclasses import dataclass
from typing import Dict, Generator, Iterable, Optional, Set, Tuple

import clingo

from ..utils import AssumptionWrapper
from .base import ExplorationStatus, Explorer

ASSUMPTION_SYMBOL_NAME = "a"
DEFAULT_LITERAL_ID = 0


@dataclass(frozen=True)
class RepresentationID:
    """ID for internal assumption representations of ExplorerASP"""

    id: int

    def __int__(self) -> int:  # nocoverage
        return self.id


@dataclass(frozen=True)
class LiteralID:
    """ID for internal literal representations of ExplorerASP"""

    id: int

    def __int__(self) -> int:  # nocoverage
        return self.id


class ExploredException(Exception):
    """The explored encoding returned unsatisfiable, this cannot be interpreted"""


class ExplorerAsp(Explorer):
    """Oracle using an ASP explore encoding for getting MUS candidates"""

    # pylint: disable=too-many-instance-attributes

    def __init__(self, assumptions: Iterable[AssumptionWrapper]) -> None:
        super().__init__(assumptions=assumptions)
        self._mus_count = 0
        self._control = clingo.Control(["--heuristic=Domain"])
        self._control.configuration.solve.models = 0  # type: ignore

        self._assumption_counter = 0
        self._assumption_to_rid: Dict[AssumptionWrapper, RepresentationID] = {}
        self._rid_to_assumption: Dict[RepresentationID, AssumptionWrapper] = {}

        self._rid_to_lid: Dict[RepresentationID, LiteralID] = {}
        self._lid_to_rid: Dict[LiteralID, RepresentationID] = {}

        # Add assumptions to control
        for assumption in self._assumptions:
            self._add_assumption(assumption)

        # Register satisfiability indicators
        (self._rid_sat, self._lid_sat), (self._rid_unsat, self._lid_unsat) = self._add_satisfiability_indicators()

    def reset(self) -> None:
        self._mus_count = 0
        self._control = clingo.Control(["--heuristic=Domain"])
        self._control.configuration.solve.models = 0  # type: ignore
        self._assumption_counter = 0

        self._assumption_to_rid = {}
        self._rid_to_assumption = {}

        self._rid_to_lid = {}
        self._lid_to_rid = {}

        # Add assumptions to control
        for assumption in self._assumptions:
            self._add_assumption(assumption)

        # Register satisfiability indicators
        (self._rid_sat, self._lid_sat), (self._rid_unsat, self._lid_unsat) = self._add_satisfiability_indicators()

    @property
    def mus_count(self) -> int:
        return self._mus_count

    def add_sat(self, assumptions: Iterable[AssumptionWrapper]) -> None:
        # take difference of subset with all assumptions
        rule_assumptions = [a for a in self.assumptions if a not in assumptions]
        rule_literal_ids = [int(self._rid_to_lid[self._assumption_to_rid[a]]) for a in rule_assumptions]
        # invert difference assumptions
        rule_body = [-lid for lid in rule_literal_ids] + [int(self._lid_sat)]
        with self._control.backend() as backend:
            backend.add_rule([], rule_body)

    def add_mus(self, assumptions: Iterable[AssumptionWrapper]) -> None:
        rule_body = [int(self._rid_to_lid[self._assumption_to_rid[a]]) for a in assumptions] + [int(self._lid_unsat)]
        with self._control.backend() as backend:
            backend.add_rule([], rule_body)
        self._mus_count += 1

    def _register_assumption_representation(self, assumption: AssumptionWrapper) -> RepresentationID:
        self._assumption_counter += 1
        representation_id = RepresentationID(self._assumption_counter)
        self._rid_to_assumption[representation_id] = assumption
        self._assumption_to_rid[assumption] = representation_id
        return representation_id

    def _compose_assumption_atom(self, assumption: AssumptionWrapper) -> clingo.Symbol:
        representation_id = self._assumption_to_rid[assumption]
        return clingo.Function(ASSUMPTION_SYMBOL_NAME, [clingo.Number(representation_id.id)])

    def _register_assumption_atom(self, assumption: AssumptionWrapper, clingo_backend: clingo.Backend) -> LiteralID:
        assumption_symbol = self._compose_assumption_atom(assumption)
        literal_id = LiteralID(clingo_backend.add_atom(assumption_symbol))
        return literal_id

    def _add_assumption(self, assumption: AssumptionWrapper) -> None:
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

    def _add_satisfiability_indicators(
        self,
    ) -> Tuple[Tuple[RepresentationID, LiteralID], Tuple[RepresentationID, LiteralID]]:
        """Adds satisfiability indicator choices (1{_sat;_unsat}) to the class control"""
        aw_sat = AssumptionWrapper(literal=DEFAULT_LITERAL_ID, symbol=clingo.parse_term("0"), sign=True)
        aw_unsat = AssumptionWrapper(literal=DEFAULT_LITERAL_ID, symbol=clingo.parse_term("1"), sign=True)
        rid_sat = self._register_assumption_representation(aw_sat)
        rid_unsat = self._register_assumption_representation(aw_unsat)
        with self._control.backend() as backend:
            lid_sat = self._register_assumption_atom(aw_sat, backend)
            lid_unsat = self._register_assumption_atom(aw_unsat, backend)
            backend.add_heuristic(int(lid_sat), clingo.backend.HeuristicType.True_, 1, 1, [])
            backend.add_heuristic(int(lid_unsat), clingo.backend.HeuristicType.True_, 1, 1, [])
            backend.add_rule(head=[int(lid_sat), int(lid_unsat)], body=[], choice=True)
            backend.add_rule(head=[], body=[-int(lid_sat), -int(lid_unsat)], choice=True)
        return (rid_sat, lid_sat), (rid_unsat, lid_unsat)

    def _get_model(self) -> Optional[Set[clingo.Symbol]]:
        with self._control.solve(assumptions=[int(self._lid_sat), int(self._lid_unsat)], yield_=True) as solve_handle:
            if solve_handle.get().satisfiable:
                symbols = solve_handle.model().symbols(atoms=True)
                symbols_cleaned = {
                    s for s in symbols if int(s.arguments[0].number) not in [int(self._rid_sat), int(self._rid_unsat)]
                }
                return symbols_cleaned
        return None

    @property
    def _symbol_unsat(self) -> clingo.Symbol:
        return clingo.parse_term(f"{ASSUMPTION_SYMBOL_NAME}({int(self._rid_unsat)})")

    @property
    def _symbol_sat(self) -> clingo.Symbol:
        return clingo.parse_term(f"{ASSUMPTION_SYMBOL_NAME}({int(self._rid_sat)})")

    def candidates(self) -> Generator[Set[AssumptionWrapper], None, None]:
        while True:
            model = self._get_model()
            if model is None:
                break
            rids = [RepresentationID(atom.arguments[0].number) for atom in model]
            yield {self._rid_to_assumption[rid] for rid in rids}

    def explored(self, assumption_set: Set[AssumptionWrapper]) -> ExplorationStatus:
        # Convert AssumptionWrappers for the assumption set to explorer literals
        a_literals = [int(self._rid_to_lid[self._assumption_to_rid[a]]) for a in assumption_set]
        # Add negated literals of remaining assumptions
        a_literals += [
            -int(self._rid_to_lid[self._assumption_to_rid[a]]) for a in self.assumptions if a not in assumption_set
        ]
        with self._control.solve(assumptions=a_literals, yield_=True) as solve_handle:
            if solve_handle.get().satisfiable:
                model_symbols = solve_handle.model().symbols(atoms=True)
                if self._symbol_sat in model_symbols and self._symbol_unsat in model_symbols:
                    return ExplorationStatus.UNKNOWN
                if self._symbol_sat in model_symbols:
                    return ExplorationStatus.UNSATISFIABLE  # nocoverage
                if self._symbol_unsat in model_symbols:
                    return ExplorationStatus.SATISFIABLE
            raise ExploredException()  # nocoverage
