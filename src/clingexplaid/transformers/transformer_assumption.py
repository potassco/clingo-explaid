"""
Transformer Module: Assumption Transformer for converting facts to choices that can be assumed
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Union

import clingo
import clingo.ast as _ast

from ..utils import get_constant_string, match_ast_symbolic_atom_signature
from ..utils.match import match
from ..utils.symbols import ast_symbolic_atom_to_symbol
from .exceptions import NotGroundedException, UntransformedException


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


class AssumptionTransformer(_ast.Transformer):
    """
    A transformer that transforms facts that match with one of the signatures provided (no signatures means all facts)
    into choice rules and also provides the according assumptions for them.
    """

    def __init__(self, filters: Optional[Iterable[Union[FilterPattern, FilterSignature]]] = None):
        self.filters: Set[Union[FilterPattern, FilterSignature]] = set(filters) if filters is not None else set()
        self.fact_rules: List[str] = []
        self.transformed: bool = False
        self.program_constants: Dict[str, str] = {}

    def _filters_apply(self, ast_symbol: _ast.ASTType.SymbolicAtom) -> bool:
        applies = False
        for symbol_filter in self.filters:
            match symbol_filter:
                case FilterPattern(pattern=pattern):
                    applies |= bool(match(pattern, ast_symbolic_atom_to_symbol(ast_symbol)))
                case FilterSignature(name=name, arity=arity):
                    applies |= match_ast_symbolic_atom_signature(ast_symbol, (name, arity))
        return applies

    def visit_Rule(self, node: clingo.ast.AST) -> clingo.ast.AST:  # pylint: disable=C0103
        """
        Transforms head of a rule into a choice rule if it is a fact and adheres to the given signatures.
        """
        if node.head.ast_type != _ast.ASTType.Literal:
            return node
        if node.body:
            return node
        filters_apply = self._filters_apply(node.head.atom)
        # if filters are defined only transform facts that match them, else transform all facts
        if self.filters and not filters_apply:
            return node

        self.fact_rules.append(str(node))

        return _ast.Rule(
            location=node.location,
            head=_ast.Aggregate(
                location=node.location,
                left_guard=None,
                elements=[node.head],
                right_guard=None,
            ),
            body=[],
        )

    def visit_Definition(self, node: clingo.ast.AST) -> clingo.ast.AST:
        """
        All defined constants of the program are stored in self.program_constants
        """
        # pylint: disable=invalid-name
        self.program_constants[node.name] = node.value.symbol
        return node

    def parse_string(self, string: str) -> str:
        """
        Function that applies the transformation to the `program_string` it's called with and returns the transformed
        program string.
        """
        out = []
        _ast.parse_string(string, lambda stm: out.append((str(self(stm)))))
        self.transformed = True
        return "\n".join(out)

    def parse_files(self, paths: Sequence[Union[str, Path]]) -> str:
        """
        Parses the files and returns a string with the transformed program.
        """
        out = []
        _ast.parse_files([str(p) for p in paths], lambda stm: out.append((str(self(stm)))))
        self.transformed = True
        return "\n".join(out)

    def get_assumption_symbols(
        self, control: clingo.Control, arguments: Optional[List[str]] = None
    ) -> Set[clingo.Symbol]:
        """
        Returns the assumption symbols which were gathered during the transformation of the program. Has to be called
        after a program has already been transformed.
        """
        # Just taking the fact symbolic atoms of the control given doesn't work here since we anticipate that
        # this control is ground on the already transformed program. This means that all facts are now choice rules
        # which means we cannot detect them like this anymore.
        if not self.transformed:
            raise UntransformedException(
                "The get_assumptions method cannot be called before a program has been transformed"
            )
        # If the control has not been grounded yet except since without grounding we don't have access to the symbolic
        # atoms.
        if len(control.symbolic_atoms) == 0:
            raise NotGroundedException(
                "The get_assumptions method cannot be called before the control has been grounded"
            )

        program_constant_strings = [get_constant_string(c, v, prefix="-c ") for c, v in self.program_constants.items()]
        fact_control_arguments = arguments if arguments is not None else []
        fact_control_arguments += program_constant_strings
        fact_control = clingo.Control(fact_control_arguments)
        fact_control.add("base", [], "\n".join(self.fact_rules))
        fact_control.ground([("base", [])])
        fact_symbols = {sym.symbol for sym in fact_control.symbolic_atoms if sym.is_fact}
        return fact_symbols

    def get_assumption_literals(self, control: clingo.Control, constants: Optional[List[str]] = None) -> Set[int]:
        """
        Returns the assumption literals which were gathered during the transformation of the program. Has to be called
        after a program has already been transformed.
        """
        assumption_symbols = self.get_assumption_symbols(control, constants)
        symbol_to_literal_lookup = {sym.symbol: sym.literal for sym in control.symbolic_atoms}
        return {symbol_to_literal_lookup[sym] for sym in assumption_symbols if sym in symbol_to_literal_lookup}
