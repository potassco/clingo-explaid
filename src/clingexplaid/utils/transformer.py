"""
Transformers for Explanation
"""

from pathlib import Path
from typing import List, Optional, Sequence, Set, Tuple, Union, Dict

import clingo
from clingo import ast as _ast

from clingexplaid.utils import match_ast_symbolic_atom_signature

RULE_ID_SIGNATURE = "_rule"


class UntransformedException(Exception):
    """Exception raised if the get_assumptions method of an AssumptionTransformer is called before it is used to
    transform a program.
    """


class RuleIDTransformer(_ast.Transformer):
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

    def visit_Rule(self, node):  # pylint: disable=C0103
        """
        Adds a rule_id_signature(id) atom to the body of every rule that is visited.
        """
        # add for each rule a theory atom (self.rule_id_signature) with the id as an argument
        symbol = _ast.Function(
            location=node.location,
            name=self.rule_id_signature,
            arguments=[
                _ast.SymbolicTerm(node.location, clingo.parse_term(str(self.rule_id)))
            ],
            external=0,
        )

        # increase the rule_id by one after every transformed rule
        self.rule_id += 1

        # insert id symbol into body of rule
        node.body.insert(len(node.body), symbol)
        return node.update(**self.visit_children(node))

    def _get_number_of_rules(self):
        return self.rule_id - 1 if self.rule_id > 1 else self.rule_id

    def parse_string(self, string: str) -> str:
        """
        Function that applies the transformation to the `program_string` it's called with and returns the transformed
        program string.
        """
        self.rule_id = 1
        out = []
        _ast.parse_string(string, lambda stm: out.append((str(self(stm)))))
        out.append(
            f"{{_rule(1..{self._get_number_of_rules()})}}"
            f" % Choice rule to allow all _rule atoms to become assumptions"
        )

        return "\n".join(out)

    def parse_file(self, path: Union[str, Path], encoding: str = "utf-8") -> str:
        """
        Parses the file at path and returns a string with the transformed program.
        """
        with open(path, "r", encoding=encoding) as f:
            return self.parse_string(f.read())

    def get_assumptions(
        self, n_rules: Optional[int] = None
    ) -> Set[Tuple[clingo.Symbol, bool]]:
        """
        Returns the rule_id_signature assumptions depending on the number of rules contained in the transformed
        program. Can only be called after parse_file has been executed before.
        """
        if n_rules is None:
            n_rules = self._get_number_of_rules()
        return {
            (clingo.parse_term(f"{self.rule_id_signature}({rule_id})"), True)
            for rule_id in range(1, n_rules + 1)
        }


class AssumptionTransformer(_ast.Transformer):
    """
    A transformer that transforms facts that match with one of the signatures provided (no signatures means all facts)
    into choice rules and also provides the according assumptions for them.
    """

    def __init__(self, signatures: Optional[Set[Tuple[str, int]]] = None):
        self.signatures = signatures if signatures is not None else set()
        self.fact_rules: List[str] = []
        self.transformed: bool = False

    def visit_Rule(self, node):  # pylint: disable=C0103
        """
        Transforms head of a rule into a choice rule if it is a fact and adheres to the given signatures.
        """
        if node.head.ast_type != _ast.ASTType.Literal:
            return node
        if node.body:
            return node
        has_matching_signature = any(
            match_ast_symbolic_atom_signature(node.head.atom, (name, arity))
            for (name, arity) in self.signatures
        )
        # if signatures are defined only transform facts that match them, else transform all facts
        if self.signatures and not has_matching_signature:
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
        _ast.parse_files(
            [str(p) for p in paths], lambda stm: out.append((str(self(stm))))
        )
        self.transformed = True
        return "\n".join(out)

    def get_assumptions(self, control: clingo.Control, constants: Optional[Dict] = None) -> Set[int]:
        """
        Returns the assumptions which were gathered during the transformation of the program. Has to be called after
        a program has already been transformed.
        """
        #  Just taking the fact symbolic atoms of the control given doesn't work here since we anticipate that
        #  this control is ground on the already transformed program. This means that all facts are now choice rules
        #  which means we cannot detect them like this anymore.
        if not self.transformed:
            raise UntransformedException(
                "The get_assumptions method cannot be called before a program has been "
                "transformed"
            )
        constant_strings = [f"-c {k}={v}" for k, v in constants.items()] if constants is not None else []
        fact_control = clingo.Control(constant_strings)
        fact_control.add("base", [], "\n".join(self.fact_rules))
        fact_control.ground([("base", [])])
        fact_symbols = [
            sym.symbol for sym in fact_control.symbolic_atoms if sym.is_fact
        ]

        symbol_to_literal_lookup = {
            sym.symbol: sym.literal for sym in control.symbolic_atoms
        }
        return {
            symbol_to_literal_lookup[sym]
            for sym in fact_symbols
            if sym in symbol_to_literal_lookup
        }


class ConstraintTransformer(_ast.Transformer):
    """
    A Transformer that takes all constraint rules and adds an atom to their head to avoid deriving false through them.
    """

    def __init__(self, constraint_head_symbol: str):
        self.constraint_head_symbol = constraint_head_symbol

    def visit_Rule(self, node):  # pylint: disable=C0103
        """
        Adds a constraint_head_symbol atom to the head of every constraint.
        """
        if node.head.ast_type != _ast.ASTType.Literal:
            return node
        if node.head.atom.ast_type != _ast.ASTType.BooleanConstant:
            return node
        if node.head.atom.value != 0:
            return node

        head_symbol = _ast.Function(
            location=node.location,
            name=self.constraint_head_symbol,
            arguments=[],
            external=0,
        )

        # insert id symbol into body of rule
        node.head = head_symbol
        return node.update(**self.visit_children(node))

    def parse_string(self, string: str) -> str:
        """
        Function that applies the transformation to the `program_string` it's called with and returns the transformed
        program string.
        """
        out = []
        _ast.parse_string(string, lambda stm: out.append((str(self(stm)))))

        return "\n".join(out)

    def parse_file(self, path: Union[str, Path], encoding: str = "utf-8") -> str:
        """
        Parses the file at path and returns a string with the transformed program.
        """
        with open(path, "r", encoding=encoding) as f:
            return self.parse_string(f.read())


__all__ = [
    RuleIDTransformer.__name__,
    AssumptionTransformer.__name__,
    ConstraintTransformer.__name__,
]
