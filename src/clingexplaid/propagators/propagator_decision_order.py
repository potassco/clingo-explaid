"""
Propagator Module: Decision Order
"""

from typing import Optional, Tuple, Set

import clingo

from .constants import UNKNOWN_SYMBOL_TOKEN, INDENT_STEP, INDENT_START, INDENT_END
from ..utils.logging import COLORS


class DecisionOrderPropagator:
    """
    Propagator for showing the Decision Order of clingo
    """

    def __init__(self, signatures: Optional[Set[Tuple[str, int]]] = None, prefix: str = ""):
        # pylint: disable=missing-function-docstring
        self.slit_symbol_lookup = {}
        self.signatures = signatures if signatures is not None else set()
        self.prefix = prefix

        self.last_decisions = []
        self.last_entailments = {}

    def init(self, init):
        """
        Method to initialize the Decision Order Propagator. Here the literals are added to the Propagator's watch list.
        """
        for atom in init.symbolic_atoms:
            program_literal = atom.literal
            solver_literal = init.solver_literal(program_literal)
            self.slit_symbol_lookup[solver_literal] = atom.symbol

        for atom in init.symbolic_atoms:
            if len(self.signatures) > 0 and not any(atom.match(name=s, arity=a) for s, a in self.signatures):
                continue
            query_program_literal = init.symbolic_atoms[atom.symbol].literal
            query_solver_literal = init.solver_literal(query_program_literal)
            init.add_watch(query_solver_literal)
            init.add_watch(-query_solver_literal)

    def _is_printed(self, symbol: clingo.Symbol) -> bool:
        """
        Helper function to check if a specific symbol should be printed or not
        """
        printed = True
        # skip UNKNOWN print if signatures is set
        if len(self.signatures) > 0 and symbol == UNKNOWN_SYMBOL_TOKEN:
            printed = False
        # skip if symbol signature is not in self.signatures
        if len(self.signatures) > 0 and symbol != UNKNOWN_SYMBOL_TOKEN:
            if not any(symbol.match(s, a) for s, a in self.signatures):
                printed = False

        return printed

    def propagate(self, control, changes) -> None:
        """
        Propagate method the is called when one the registered literals is propagated by clasp. Here useful information
        about the decision progress is recorded to be visualized later.
        """
        # pylint: disable=unused-argument
        decisions, entailments = self.get_decisions(control.assignment)

        print_level = 0
        for d in decisions:
            print_level += 1
            if d in self.last_decisions:
                continue

            decision_symbol = self.get_symbol(d)
            decision_printed = self._is_printed(decision_symbol)
            decision_negative = d < 0

            # build decision indent string
            decision_indent_string = INDENT_START + INDENT_STEP * (print_level - 1)
            # print decision if it matches the signatures (if provided)
            if decision_printed:
                print(
                    f"{self.prefix}{decision_indent_string}"
                    f"[{['+', '-'][int(decision_negative)]}]"
                    f" {decision_symbol} "
                    f"[{d}]"
                )

            entailment_list = entailments[d] if d in entailments else []
            # build entailment indent string
            entailment_indent_string = (
                (INDENT_START + INDENT_STEP * (print_level - 2) + INDENT_END) if print_level > 1 else "│ "
            )
            for e in entailment_list:
                # skip decision in entailments
                if e == d:
                    continue
                entailment_symbol = self.get_symbol(e)
                entailment_printed = self._is_printed(entailment_symbol)
                # skip if entailment symbol doesn't mach signatures (if provided)
                if not entailment_printed:
                    continue

                entailment_negative = e < 0
                if decision_printed:
                    print(
                        f"{self.prefix}{entailment_indent_string}{COLORS['GREY']}"
                        f"[{['+', '-'][int(entailment_negative)]}] "
                        f"{entailment_symbol} "
                        f"[{e}]{COLORS['NORMAL']}"
                    )

        self.last_decisions = decisions
        self.last_entailments = entailments

    def undo(self, thread_id: int, assignment, changes) -> None:
        """
        This function is called when one of the solvers decisions is undone.
        """
        # pylint: disable=unused-argument

        if len(self.last_decisions) < 1:
            return
        decision = self.last_decisions[-1]
        decision_symbol = self.get_symbol(decision)

        # don't print decision undo if its signature is not matching the provided ones
        printed = self._is_printed(decision_symbol)

        indent_string = INDENT_START + INDENT_STEP * (len(self.last_decisions) - 1)
        if printed:
            print(f"{self.prefix}{indent_string}{COLORS['RED']}[✕] {decision_symbol} [{decision}]{COLORS['NORMAL']}")
        self.last_decisions = self.last_decisions[:-1]

    @staticmethod
    def get_decisions(assignment):
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

    def get_symbol(self, literal) -> clingo.Symbol:
        """
        Helper function to get a literal's associated symbol.
        """
        try:
            if literal > 0:
                symbol = self.slit_symbol_lookup[literal]
            else:
                # negate symbol
                symbol = clingo.parse_term(str(self.slit_symbol_lookup[-literal]))
        except KeyError:
            # internal literals
            symbol = UNKNOWN_SYMBOL_TOKEN
        return symbol
