from typing import List, Optional, Tuple, Set

import clingo

from .logger import COLORS

DecisionLevel = List[int]
DecisionLevelList = List[DecisionLevel]

UNKNOWN_SYMBOL_TOKEN = "INTERNAL"

INDENT_START = "├─"
INDENT_STEP = f"─{COLORS['GREY']}┼{COLORS['NORMAL']}──"
INDENT_END = f"─{COLORS['GREY']}┤{COLORS['NORMAL']}  "


class DecisionOrderPropagator:
    def __init__(
        self, signatures: Optional[Set[Tuple[str, int]]] = None, prefix: str = ""
    ):
        self.slit_symbol_lookup = {}
        self.signatures = signatures if signatures is not None else set()
        self.prefix = prefix

        self.last_decisions = []
        self.last_entailments = {}

    def init(self, init):
        for atom in init.symbolic_atoms:
            program_literal = atom.literal
            solver_literal = init.solver_literal(program_literal)
            self.slit_symbol_lookup[solver_literal] = atom.symbol

        for atom in init.symbolic_atoms:
            if len(self.signatures) > 0 and not any(
                atom.match(name=s, arity=a) for s, a in self.signatures
            ):
                continue
            query_program_literal = init.symbolic_atoms[atom.symbol].literal
            query_solver_literal = init.solver_literal(query_program_literal)
            init.add_watch(query_solver_literal)
            init.add_watch(-query_solver_literal)

    def propagate(self, control, changes) -> None:
        decisions, entailments = self.get_decisions(control.assignment)

        print_level = 0
        for d in decisions:
            print_level += 1
            if d in self.last_decisions:
                continue
            decision_symbol = self.get_symbol(d)

            # don't print decision if its signature is not matching the provided ones
            skip_print = False
            if len(self.signatures) > 0 and decision_symbol != UNKNOWN_SYMBOL_TOKEN:
                if not any(decision_symbol.match(s, a) for s, a in self.signatures):
                    skip_print = True

            decision_negative = d < 0

            indent_string = INDENT_START + INDENT_STEP * (print_level - 1)
            if not skip_print:
                print(
                    f"{self.prefix}{indent_string}[{['+', '-'][int(decision_negative)]}] {decision_symbol} [{d}]"
                )
            entailment_list = entailments[d] if d in entailments else []
            for e in entailment_list:
                if e == d:
                    continue
                entailment_indent = (
                    (INDENT_START + INDENT_STEP * (print_level - 2) + INDENT_END)
                    if print_level > 1
                    else "│ "
                )
                entailment_symbol = self.get_symbol(e)
                entailment_negative = e < 0
                if not skip_print:
                    print(
                        f"{self.prefix}{entailment_indent}{COLORS['GREY']}[{['+', '-'][int(entailment_negative)]}] "
                        f"{entailment_symbol} [{e}]{COLORS['NORMAL']}"
                    )

        self.last_decisions = decisions
        self.last_entailments = entailments

    def undo(self, thread_id: int, assignment, changes) -> None:
        if len(self.last_decisions) < 1:
            return
        decision = self.last_decisions[-1]
        decision_symbol = self.get_symbol(decision)

        # don't print decision undo if its signature is not matching the provided ones
        skip_print = False
        if len(self.signatures) > 0 and decision_symbol != UNKNOWN_SYMBOL_TOKEN:
            if not any(decision_symbol.match(s, a) for s, a in self.signatures):
                skip_print = True

        indent_string = INDENT_START + INDENT_STEP * (len(self.last_decisions) - 1)
        if not skip_print:
            print(
                f"{self.prefix}{indent_string}{COLORS['RED']}[✕] {decision_symbol} [{decision}]{COLORS['NORMAL']}"
            )
        self.last_decisions = self.last_decisions[:-1]

    @staticmethod
    def get_decisions(assignment):
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
                    entailments[decision] = trail[
                        (level_offset_start + 1) : level_offset_end
                    ]
                level += 1
        except RuntimeError:
            return decisions, entailments

    def get_symbol(self, literal) -> clingo.Symbol:
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
