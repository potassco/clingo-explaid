"""
Propagator Module: Decision Order
"""

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Sequence, Set, Tuple, Union

import clingo
from clingo import Propagator

INTERNAL_STRING = "INTERNAL"


@dataclass
class Decision:
    positive: bool
    literal: int
    symbol: Optional[clingo.Symbol]

    def __str__(self) -> str:
        symbol_string = str(self.symbol) if self.symbol is not None else INTERNAL_STRING
        return f"({[" - ", " + "][self.positive]}{symbol_string})"


class SolverDecisionPropagator(Propagator):
    """
    Propagator for showing the Solver Decisions of clingo
    """

    def __init__(
        self,
        signatures: Optional[Set[Tuple[str, int]]] = None,
        callback_propagate: Optional[Callable] = None,
        callback_undo: Optional[Callable] = None,
    ):
        # pylint: disable=missing-function-docstring
        self.literal_symbol_lookup: Dict[int, clingo.Symbol] = {}
        self.signatures = signatures if signatures is not None else set()

        self.callback_propagate: Callable = callback_propagate if callback_propagate is not None else lambda x: None
        self.callback_undo: Callable = callback_undo if callback_undo is not None else lambda x: None

    def init(self, init: clingo.PropagateInit) -> None:
        """
        Method to initialize the Decision Order Propagator. Here the literals are added to the Propagator's watch list.
        """
        for atom in init.symbolic_atoms:
            program_literal = atom.literal
            solver_literal = init.solver_literal(program_literal)
            self.literal_symbol_lookup[solver_literal] = atom.symbol

        for atom in init.symbolic_atoms:
            if len(self.signatures) > 0 and not any(atom.match(name=s, arity=a) for s, a in self.signatures):
                continue
            symbolic_atom = init.symbolic_atoms[atom.symbol]
            if symbolic_atom is None:
                continue  # nocoverage
            query_program_literal = symbolic_atom.literal
            query_solver_literal = init.solver_literal(query_program_literal)
            init.add_watch(query_solver_literal)
            init.add_watch(-query_solver_literal)

    def propagate(self, control: clingo.PropagateControl, changes: Sequence[int]) -> None:
        """
        Propagate method the is called when one the registered literals is propagated by clasp. Here useful information
        about the decision progress is recorded to be visualized later.
        """
        # pylint: disable=unused-argument
        decisions, entailments = self.get_decisions(control.assignment)

        literal_sequence = []
        for d in decisions:
            literal_sequence.append(d)
            if d in entailments:
                literal_sequence.append(list(entailments[d]))
        decision_sequence = self.literal_to_decision_sequence(literal_sequence)

        self.callback_propagate(decision_sequence)

    def undo(self, thread_id: int, assignment: clingo.Assignment, changes: Sequence[int]) -> None:
        """
        This function is called when one of the solvers decisions is undone.
        """
        # pylint: disable=unused-argument

        self.callback_undo()

    def literal_to_decision(self, literal: int) -> Decision:
        is_positive = literal >= 0
        symbol = self.literal_symbol_lookup.get(abs(literal))
        return Decision(literal=abs(literal), positive=is_positive, symbol=symbol)

    def literal_to_decision_sequence(
        self, literal_sequence: List[Union[int, List[int]]]
    ) -> List[Union[Decision, List[Decision]]]:
        new_decision_sequence = []
        for element in literal_sequence:
            if isinstance(element, int):
                new_decision_sequence.append(self.literal_to_decision(element))
            elif isinstance(element, list):
                new_decision_sequence.append([self.literal_to_decision(literal) for literal in element])
        return new_decision_sequence

    @staticmethod
    def get_decisions(assignment: clingo.Assignment) -> Tuple[List[int], Dict[int, List[int]]]:
        """
        Helper function to extract a list of decisions and entailments from a clingo propagator assignment.
        """
        level = 0
        decisions = []
        entailments = {}
        try:
            while True:
                decision = assignment.decision(level)
                decisions.append(decision)

                trail = assignment.trail
                level_offset_start = trail.begin(level)
                level_offset_end = trail.end(level)
                level_offset_diff = level_offset_end - level_offset_start
                if level_offset_diff > 1:
                    entailments[decision] = trail[(level_offset_start + 1) : level_offset_end]
                level += 1
        except RuntimeError:
            return decisions, entailments
