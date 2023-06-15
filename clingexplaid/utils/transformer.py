import clingo
from clingo.ast import Transformer, parse_string, ASTType
from clingo import ast as _ast
from typing import List, Tuple, Optional
from dataclasses import dataclass


RULE_ID_SIGNATURE = "_rule"


@dataclass
class TransformerResult:
    """
    Returned by transformers. Is a python dataclass that encapsulates the transformed program-string and output
    assumptions if there are any.
    """
    output_string: str
    output_assumptions: Optional[List[Tuple[clingo.Symbol, bool]]]


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

    def get_transformed(self, program_string: str) -> TransformerResult:
        """
        Function that applies the transformation on the `program_string` it's called with and returns a
        TransformerResult with the transformed program-string and the necessary assumptions for the
        `self.rule_id_signature` atoms.
        """
        self.rule_id = 1
        out = []
        parse_string(program_string, lambda stm: out.append((str(self(stm)))))
        out.append(f"{{_rule(1..{self.rule_id})}} % Choice rule to allow all _rule atoms to become assumptions")

        result = TransformerResult(
            output_string="\n".join(out),
            output_assumptions=self._get_assumptions(self.rule_id)
        )
        return result

    def _get_assumptions(self, n_rules) -> List[Tuple[clingo.Symbol, bool]]:
        return [(clingo.parse_term(f"{self.rule_id_signature}({rule_id})"), True) for rule_id in range(1, n_rules)]
