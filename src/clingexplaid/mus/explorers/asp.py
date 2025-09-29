"""Explorer using ASP for getting MUS candidates"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Generator, Iterable, Optional, Set, Tuple

import clingo
from clingo import MessageCode

from ..utils import AssumptionWrapper
from .base import ExplorationStatus, Explorer

ASSUMPTION_SYMBOL_NAME = "a"
PATH_ENCODING_EXPLORED = str(Path(__file__).parent.parent / "encodings/explored.lp")
EXPLORED_ATOM_SAT = "explored(sat)"
EXPLORED_ATOM_UNSAT = "explored(unsat)"


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

    def __init__(self, assumptions: Iterable[AssumptionWrapper]) -> None:
        super().__init__(assumptions=assumptions)
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

    def add_sat(self, assumptions: Iterable[AssumptionWrapper]) -> None:
        super().add_sat(assumptions)
        # take difference of subset with all assumptions
        rule_assumptions = [a for a in self.assumptions if a not in assumptions]
        rule_literal_ids = [int(self._rid_to_lid[self._assumption_to_rid[a]]) for a in rule_assumptions]
        # invert difference assumptions
        rule_body = [-lid for lid in rule_literal_ids]
        with self._control.backend() as backend:
            backend.add_rule([], rule_body)

    def add_mus(self, assumptions: Iterable[AssumptionWrapper]) -> None:
        super().add_mus(assumptions)
        rule_body = [int(self._rid_to_lid[self._assumption_to_rid[a]]) for a in assumptions]
        with self._control.backend() as backend:
            backend.add_rule([], rule_body)

    def _get_model(self) -> Optional[Set[clingo.Symbol]]:
        with self._control.solve(yield_=True) as solve_handle:
            if solve_handle.get().satisfiable:
                return set(solve_handle.model().symbols(atoms=True))
        return None

    def candidates(self) -> Generator[Set[AssumptionWrapper], None, None]:
        while True:
            model = self._get_model()
            if model is None:
                break
            rids = [RepresentationID(int(str(atom.arguments[0]))) for atom in model]
            yield {self._rid_to_assumption[rid] for rid in rids}

    def explored(self, assumption_set: Set[AssumptionWrapper]) -> ExplorationStatus:
        ctl = clingo.Control(logger=silent_logger)
        ctl.load(PATH_ENCODING_EXPLORED)
        rules, test_string = self._get_explored_rules(assumption_set=assumption_set)
        if len(rules) == 0:
            return ExplorationStatus.UNKNOWN

        ctl.add("base", [], "\n".join(rules))
        ctl.add("base", [], test_string)
        ctl.ground([("base", [])])

        with ctl.solve(yield_=True) as solve_handle:
            if solve_handle.get().satisfiable:
                atoms = [str(a) for a in solve_handle.model().symbols(atoms=True)]
                if EXPLORED_ATOM_SAT in atoms:  # nocoverage
                    return ExplorationStatus.SATISFIABLE
                if EXPLORED_ATOM_UNSAT in atoms:  # nocoverage
                    return ExplorationStatus.UNSATISFIABLE
                return ExplorationStatus.UNKNOWN
            raise ExploredException()  # nocoverage

    def _get_explored_rules(self, assumption_set: set[AssumptionWrapper]) -> Tuple[Set[str], str]:
        """Helper returning the asp rules of the already found subsets and the test string for the explored encoding"""
        rules = set()
        for i, mus in enumerate(self._found_mus):
            rule_string = " ".join(f"unsat({i},{a.literal})." for a in mus)
            rules.add(rule_string)
        for i, sat in enumerate(self._found_sat):
            rule_string = " ".join(f"sat({i},{a.literal})." for a in sat)
            rules.add(rule_string)
        test_string = " ".join(f"test({a.literal})." for a in assumption_set)
        return rules, test_string


def silent_logger(code: MessageCode, message: str) -> None:  # pylint: disable=unused-argument
    """Logger that is completely silent, for a clingo.Control object"""
    return
