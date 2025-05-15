"""
Transformer Module: Assumption Transformer for converting facts to choices that can be assumed
"""

import warnings
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Set, Tuple, Union

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
        self._parsed_rules: List[str] = []
        self._constants: Dict[str, clingo.Symbol] = {}
        self._assumptions: Set[Tuple[clingo.Symbol, bool]] = set()

    @staticmethod
    def _to_symbol(symbol: clingo.ast.ASTType.SymbolicAtom) -> Optional[Set[clingo.Symbol]]:
        return {clingo.parse_term(str(symbol))}

    @staticmethod
    def _to_ast(symbol: Union[str, clingo.Symbol]) -> clingo.ast.AST:
        parsed_ast: List[clingo.ast.AST] = []
        parse_string(f"{symbol}.", parsed_ast.append)
        ast_symbol = parsed_ast[1]  # return AST symbol (parsed_ast[0] = '#program base.')
        return ast_symbol

    def _add_assumption(self, symbol: clingo.Symbol, positive: bool) -> None:
        self._assumptions.add((symbol, positive))

    def _add_assumption_string(self, string: str, positive: bool) -> None:
        self._add_assumption(clingo.parse_term(string), positive)

    def _add_constant(self, name: str, symbol: clingo.Symbol) -> None:
        self._constants[name] = symbol

    def _any_filters_apply(self, symbol: clingo.Symbol) -> bool:
        applies = False
        # TODO : if filters is none always false
        for symbol_filter in self.filters:
            match symbol_filter:
                case FilterPattern(pattern=pattern):
                    applies |= bool(match(pattern, symbol))
                case FilterSignature(name=name, arity=arity):
                    applies |= len(symbol.arguments) == arity and symbol.name == name
        return applies

    @staticmethod
    def _unpool(ast_symbol: clingo.ast.ASTType.SymbolicAtom) -> Set[clingo.Symbol]:
        if ".." in str(ast_symbol):
            # Case range in ast symbol (i.e. 1..10)
            # TODO : solved using grounding but if possible I'd rather avoid this
            unpool_control = clingo.Control()
            unpool_control.add(f"{ast_symbol}.")
            unpool_control.ground([("base", [])])
            with unpool_control.solve(yield_=True) as solve_handle:
                result = solve_handle.get()
                if result.satisfiable:
                    model = solve_handle.model()
                    return set(model.symbols(atoms=True))
                raise ValueError("Provided AST symbol does not follow valid ASP syntax")
        # Case default
        atoms_unpooled = ast_symbol.unpool()
        return {clingo.parse_term(str(a)) for a in atoms_unpooled}

    def _transform_rule(self, rule: clingo.ast.ASTType.Rule) -> List[clingo.ast.ASTType.Rule]:
        if rule.head.ast_type != clingo.ast.ASTType.Literal:
            return [rule]
        if rule.body:
            return [rule]

        atoms_unpooled = AssumptionPreprocessor._unpool(rule.head)
        atoms_choice: Set[clingo.ast.AST] = set()
        atoms_retained: Set[clingo.Symbol] = set()
        for atom in atoms_unpooled:
            filters_apply = self._any_filters_apply(atom)
            # if filters are defined, only transform facts that match them, else transform all facts
            if self.filters and not filters_apply:
                atoms_retained.add(atom)
                continue
            ast = AssumptionPreprocessor._to_ast(atom)
            ast_choice_literal = clingo.ast.ConditionalLiteral(location=rule.location, literal=ast.head, condition=[])
            atoms_choice.add(ast_choice_literal)
        atoms_retained_ast: Set[clingo.ast.AST] = set()
        for atom in atoms_retained:
            atoms_retained_ast.add(AssumptionPreprocessor._to_ast(atom))

        if len(atoms_choice) > 0:
            # Add all choice atoms to the assumption list
            for a_choice in atoms_choice:
                self._add_assumption_string(str(a_choice), True)

            choice_rule = clingo.ast.Rule(
                location=rule.location,
                head=clingo.ast.Aggregate(
                    location=rule.location,
                    left_guard=None,
                    elements=list(sorted(atoms_choice, key=lambda x: str(x))),
                    right_guard=None,
                ),
                body=[],
            )
            return [choice_rule, *atoms_retained_ast]
        return list(atoms_retained_ast)

    def register_ast(self, ast: clingo.ast.AST, builder: clingo.ast.ProgramBuilder) -> None:
        """Registers the provided AST to the builder and the parsed rules list"""
        if ast.ast_type == clingo.ast.ASTType.Definition:
            self._constants[ast.name] = ast.value.symbol
        self._parsed_rules.append(str(ast))
        # TODO: For some reason the builder add doesn't seem to work here since it's not added to the controls base
        #  program
        builder.add(ast)

    def process(self, program_string: str) -> str:
        """Processes the provided program string and returns the transformed program string (control is also updated)"""
        control = clingo.Control("0")
        ast_list: List[clingo.ast.AST] = []
        with ProgramBuilder(control) as builder:
            parse_string(program_string, ast_list.append)
            for ast in ast_list:
                if ast.ast_type == clingo.ast.ASTType.Rule:
                    for new_ast in self._transform_rule(ast):
                        if new_ast.ast_type != clingo.ast.ASTType.Rule:
                            new_rule = clingo.ast.Rule(location=ast.location, head=new_ast, body=[])
                            self.register_ast(new_rule, builder)
                        else:
                            self.register_ast(new_ast, builder)
                elif ast.ast_type == clingo.ast.ASTType.Definition:
                    # TODO : Here was some special handling before, maybe this needs to be reimplemented
                    self.register_ast(ast, builder)
                else:
                    self.register_ast(ast, builder)
        self._processed = True
        return "\n".join(self._parsed_rules)

    @property
    def assumptions(self) -> Set[Tuple[clingo.Symbol, bool]]:
        """Property that returns the assumptions generated by the preprocessor after calling `process`"""
        if not self._processed:
            if self._fail_on_unprocessed:
                raise UnprocessedException(
                    "It is impossible to retrieve assumptions without invoking the `process` function first"
                )
            warnings.warn(
                "Unprocessed Error: It is impossible to retrieve assumptions without invoking the "
                "`process` function first"
            )
        return set(self._assumptions)

    @property
    def constants(self) -> Dict[str, clingo.Symbol]:
        """Property that returns the constants generated by the preprocessor after calling `process`"""
        if not self._processed:
            if self._fail_on_unprocessed:
                raise UnprocessedException(
                    "It is impossible to retrieve constants without invoking the `process` function first"
                )
            warnings.warn(
                "Unprocessed Error: It is impossible to retrieve constants without invoking the "
                "`process function first`"
            )
        return self._constants
