import clingo
from clingo.ast import Transformer, parse_string, ASTType
from clingo import ast as _ast
from typing import List, Tuple, Optional, Union, Set
from dataclasses import dataclass
from pathlib import Path

from clingexplaid.utils import match_ast_symbolic_atom_signature


RULE_ID_SIGNATURE = "_rule"


class UntransformedException(Exception):
    """Exception raised if the get_assumptions method of an AssumptionTransformer is called before it is used to
    transform a program.
    """


class RuleIDTransformer(Transformer):
    """
    A Transformer that takes all the rules of a program and adds an atom with `self.rule_id_signature` in their bodys,
    to make the original rule the generated them identifiable even after grounding. Additionally, a choice rule
    containing all generated `self.rule_id_signature` atoms is added, which allows us to add assumptions that assume
    them. This is done in order to not modify the original program's reasoning by assuming all `self.rule_id_signature`
    atoms as True.
    """

    def __init__(self, rule_id_signature: str = RULE_ID_SIGNATURE):
        self.rule_id = 0
        self.rule_id_signature = rule_id_signature

    def visit_Rule(self, node):
        # add for each rule a theory atom (self.rule_id_signature) with the id as an argument
        symbol = _ast.Function(
            location=node.location,
            name=self.rule_id_signature,
            arguments=[_ast.SymbolicTerm(node.location, clingo.parse_term(str(self.rule_id)))],
            external=0)

        # increase the rule_id by one after every transformed rule
        self.rule_id += 1

        # insert id symbol into body of rule
        node.body.insert(len(node.body), symbol)
        return node.update(**self.visit_children(node))

    def get_transformed_string(self, program_string: str) -> str:
        """
        Function that applies the transformation on the `program_string` it's called with and returns a
        TransformerResult with the transformed program-string and the necessary assumptions for the
        `self.rule_id_signature` atoms.
        """
        self.rule_id = 1
        out = []
        parse_string(program_string, lambda stm: out.append((str(self(stm)))))
        out.append(f"{{_rule(1..{self.rule_id})}} % Choice rule to allow all _rule atoms to become assumptions")

        return "\n".join(out)

    def get_transformed_assumptions(self, n_rules: Optional[int] = None) -> List[Tuple[clingo.Symbol, bool]]:
        if n_rules is None:
            n_rules = self.rule_id
        return [(clingo.parse_term(f"{self.rule_id_signature}({rule_id})"), True) for rule_id in range(1, n_rules)]


class AssumptionTransformer(Transformer):

    def __init__(self, signatures: List[Tuple[str, int]]):
        self.signatures = signatures
        self.fact_rules = []

    def visit_Rule(self, node):
        if node.head.ast_type != ASTType.Literal:
            return node
        if node.body:
            return node
        has_matching_signature = any(
            [match_ast_symbolic_atom_signature(node.head.atom, (name, arity)) for (name, arity) in self.signatures])
        if not has_matching_signature:
            return node

        self.fact_rules.append(str(node))

        return _ast.Rule(
            location=node.location,
            head=_ast.Aggregate(
                location=node.location,
                left_guard=None,
                elements=[node.head],
                right_guard=None
            ),
            body=[]
        )

    def parse_string(self, string: str) -> str:
        out = []
        parse_string(string, lambda stm: out.append((str(self(stm)))))
        return "\n".join(out)

    def parse_file(self, path: Union[str, Path]) -> str:
        with open(path, "r") as f:
            return self.parse_string(f.read())

    def get_assumptions(self, control: clingo.Control) -> Set[int]:
        #  Just taking the fact symbolic atoms of the control given doesn't work here since we anticipate that
        #  this control is ground on the already transformed program. This means that all facts are now choice rules
        #  which means we cannot detect them like this anymore.
        if not self.fact_rules:
            raise UntransformedException("The get_assumptions method cannot be called before a program has been "
                                         "transformed")
        fact_control = clingo.Control()
        fact_control.add("base", [], "\n".join(self.fact_rules))
        fact_control.ground([("base", [])])
        fact_symbols = [sym.symbol for sym in fact_control.symbolic_atoms if sym.is_fact]

        symbol_to_literal_lookup = {sym.symbol: sym.literal for sym in control.symbolic_atoms}
        return {symbol_to_literal_lookup.get(sym) for sym in fact_symbols}


class ConstraintTransformer(Transformer):
    """
    A Transformer that takes all constraint rules and adds an atom to their head to avoid deriving false through them.
    """

    def __init__(self, constraint_head_symbol: str):
        self.constraint_head_symbol = constraint_head_symbol

    def visit_Rule(self, node):
        if node.head.ast_type != ASTType.Literal:
            return node
        if node.head.atom.ast_type != ASTType.BooleanConstant:
            return node
        if node.head.atom.value != 0:
            return node
        
        head_symbol = _ast.Function(
            location=node.location,
            name=self.constraint_head_symbol,
            arguments=[],
            external=0)

        # insert id symbol into body of rule
        node.head = head_symbol
        return node.update(**self.visit_children(node))

    def get_transformed_string(self, program_string: str) -> str:
        out = []
        parse_string(program_string, lambda stm: out.append((str(self(stm)))))

        return "\n".join(out)


__all__ = [
    RuleIDTransformer.__name__,
    AssumptionTransformer.__name__,
    ConstraintTransformer.__name__,
]
