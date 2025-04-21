"""
Transformer Module: Assumption Transformer for converting facts to choices that can be assumed
"""

import warnings
from dataclasses import dataclass
from typing import Iterable, Optional, Set, Union

import clingo
from clingo.ast import ProgramBuilder, parse_string

from ..exceptions import UnprocessedException
from ..utils.match import match


@dataclass
class FilterSignature:
    """Filters the facts converted to assumptions by signature"""

    name: str
    arity: int

    def __hash__(self) -> int:
        return hash((self.name, self.arity))


@dataclass
class FilterPattern:
    """Filters the facts converted to assumptions by pattern"""

    pattern: str

    def __hash__(self) -> int:
        return hash(self.pattern)


class AssumptionPreprocessor:
    """
    A transformer that transforms facts that match with one of the signatures provided (no signatures means all facts)
    into choice rules and also provides the according assumptions for them.
    """

    def __init__(
        self,
        filters: Optional[Iterable[Union[FilterPattern, FilterSignature]]] = None,
        control: Optional[clingo.Control] = None,
        fail_on_unprocessed: bool = True,
    ):
        self.control = control if control is not None else clingo.Control()
        self.filters: Set[Union[FilterPattern, FilterSignature]] = set(filters) if filters is not None else set()
        self._processed = False
        self._fail_on_unprocessed = fail_on_unprocessed

    @staticmethod
    def _to_symbol(symbol: clingo.ast.ASTType.SymbolicAtom) -> clingo.Symbol:
        return clingo.parse_term(str(symbol))

    def _any_filters_apply(self, ast_symbol: clingo.ast.ASTType.SymbolicAtom):
        applies = False
        for symbol_filter in self.filters:
            match symbol_filter:
                case FilterPattern(pattern=pattern):
                    applies |= bool(match(pattern, AssumptionPreprocessor._to_symbol(ast_symbol)))
                case FilterSignature(name=name, arity=arity):
                    symbol = AssumptionPreprocessor._to_symbol(ast_symbol)
                    applies |= len(symbol.arguments) == arity and symbol.name == name
        return applies

    def _transform_rule(self, rule: clingo.ast.ASTType.Rule):
        if rule.head.ast_type != clingo.ast.ASTType.Literal:
            return rule
        if rule.body:
            return rule

        atoms_unpooled = rule.head.unpool()
        atoms_choice = set()
        atoms_retained = set()
        for atom in atoms_unpooled:
            filters_apply = self._any_filters_apply(atom)
            # if filters are defined only transform facts that match them, else transform all facts
            if self.filters and not filters_apply:
                atoms_retained.add(atom)
                continue
            new_choice_literal = clingo.ast.ConditionalLiteral(location=rule.location, literal=atom, condition=[])
            atoms_choice.add(new_choice_literal)

        if len(atoms_choice) > 0:
            choice_rule = clingo.ast.Rule(
                location=rule.location,
                head=clingo.ast.Aggregate(
                    location=rule.location,
                    left_guard=None,
                    elements=list(atoms_choice),
                    right_guard=None,
                ),
                body=[],
            )
            return [choice_rule, *atoms_retained]
        else:
            return atoms_retained

    def process(self, program_string: str) -> None:
        control = clingo.Control("0")
        ast_list = []
        with ProgramBuilder(control) as builder:
            parse_string(program_string, lambda x: ast_list.append(x))
            for ast in ast_list:
                if ast.ast_type == clingo.ast.ASTType.Rule:
                    for new_ast in self._transform_rule(ast):
                        if new_ast.ast_type != clingo.ast.ASTType.Rule:
                            new_rule = clingo.ast.Rule(location=ast.location, head=new_ast, body=[])
                            print(new_rule)  # TODO : Rule Recording
                            builder.add(new_rule)
                        else:
                            print(new_ast)  # TODO : Rule Recording
                            builder.add(new_ast)
                elif ast.ast_type == clingo.ast.ASTType.Definition:
                    warnings.warn("TO BE IMPLEMENTED")  # TODO : Implement
                else:
                    builder.add(ast)
        self._processed = True

    @property
    def assumptions(self) -> Set[clingo.Symbol]:
        if not self._processed:
            if self._fail_on_unprocessed:
                raise UnprocessedException(
                    "It is impossible to retrieve assumptions without invoking the " "'process' function first"
                )
            else:
                warnings.warn(
                    "Unprocessed Error: It is impossible to retrieve assumptions without invoking the "
                    "'process' function first"
                )
        warnings.warn("Not Implemented")
        return set()
