import clingo
from clingo.ast import Transformer, parse_string, ASTType
from clingo import ast as _ast
from typing import List, Tuple, Optional
from dataclasses import dataclass


RULE_ID_SIGNATURE = "_rule"


@dataclass
class Signature:
    """
    Defines a signature of an atom in clingo.
    """
    name: str
    arity: int


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

    def get_transformer_result(self, program_string: str) -> TransformerResult:
        result = TransformerResult(
            output_string=self.get_transformed_string(program_string=program_string),
            output_assumptions=self.get_transformed_assumptions()
        )
        return result


class SignatureToAssumptionTransformer(Transformer):
    """
    A Transformer to select a set of signatures of a program and convert all facts that match this signature into
    assumptions. This also makes it necessary to make them available in a choice rule, which, if not already present,
    has to be added. Since it's hard to check if a certain fact is covered by a choice rule in the program we just
    simply add a choice rule for each fact by default.
    """

    def __init__(self, program_string: str, signatures: List[Signature]):
        self.signatures = signatures
        self.program_string = program_string
        self.facts = self.get_facts()

    def get_facts(self, ctl) -> List[clingo.Symbol]:
        ctl = clingo.Control()
        ctl.add("base", [], self.program_string)
        ctl.ground([("base", [])])
        return [sym.symbol for sym in ctl.symbolic_atoms if sym.is_fact]

    def visit_Rule(self, node):
        print(node.head, node.head.ast_type)
        if node.head.ast_type == ASTType.Literal and not node.body:
            # TODO: Match the head symbol to the looked for signatures here. But how can I match AST Symbols?
            print("---", node.head.atom.symbol)
            return None  # TODO: How do I return nothing (like None)
        return node

    def get_transformed(self) -> TransformerResult:
        out = [f"{{{str(fact)}}}." for fact in self.facts]
        parse_string(self.program_string, lambda stm: out.append((str(self(stm)))))

        result = TransformerResult(
            output_string="\n".join(out),
            output_assumptions=None
        )
        return result


prg = """
cat(1).
cat(2).
{dog(1..10)}.
mantis(1). mantis(2).
axolotl(X) :- X=1..5. 

something_true.
bike(1); snake(1) :- something_true.
"""


rt = RuleIDTransformer()
res = rt.get_transformer_result(prg)
print(res.output_string)
print(res.output_assumptions)

print("-" * 50)

at = SignatureToAssumptionTransformer(
    program_string=prg,
    signatures=[
        Signature(name='cat', arity=1),
        Signature(name='dog', arity=1),
        Signature(name='mantis', arity=1),
        Signature(name='axolotl', arity=1),
        Signature(name='something_true', arity=0),
        Signature(name='snake', arity=1),
    ]
)
res = at.get_transformed()
print(res.output_string)
