"""
Tests for the transformers package
"""

from unittest import TestCase

import clingo

from clingexplaid.transformers import (
    AssumptionTransformer,
    ConstraintTransformer,
    FactTransformer,
    OptimizationRemover,
    RuleIDTransformer,
    RuleSplitter,
)
from clingexplaid.transformers.exceptions import NotGroundedException, UntransformedException
from clingexplaid.transformers.transformer_assumption import FilterPattern, FilterSignature

from .test_main import TEST_DIR, read_file


class TestTransformers(TestCase):
    """
    Test cases for transformers.
    """

    # ASSUMPTION TRANSFORMER

    def test_assumption_transformer_parse_file(self) -> None:
        """
        Test the AssumptionTransformer's `parse_file` method.
        """
        program_path = TEST_DIR.joinpath("res/test_program.lp")
        program_path_transformed = TEST_DIR.joinpath("res/transformed_program_assumptions_certain_signatures.lp")
        filters = [FilterSignature(c, 1) for c in "abcdef"]
        at = AssumptionTransformer(filters=filters)
        result = at.parse_files([program_path])
        self.assertEqual(result.strip(), read_file(program_path_transformed).strip())

    def test_assumption_transformer_parse_file_no_signatures(self) -> None:
        """
        Test the AssumptionTransformer's `parse_file` method with no signatures provided.
        """
        program_path = TEST_DIR.joinpath("res/test_program.lp")
        program_path_transformed = TEST_DIR.joinpath("res/transformed_program_assumptions_all.lp")
        at = AssumptionTransformer()
        result = at.parse_files([program_path])
        self.assertEqual(result.strip(), read_file(program_path_transformed).strip())

    def test_assumption_transformer_parse_pattern_filter(self) -> None:
        """
        Test the AssumptionTransformer's `parse_file` method with no signatures provided.
        """
        program_path = TEST_DIR.joinpath("res/test_program_pattern.lp")
        program_path_transformed = TEST_DIR.joinpath("res/transformed_program_pattern.lp")
        at = AssumptionTransformer(filters={FilterPattern("a(_,value,_)")})
        result = at.parse_files([program_path])
        self.assertEqual(result.strip(), read_file(program_path_transformed).strip())

    def test_assumption_transformer_get_assumptions_before_transformation(self) -> None:
        """
        Test the AssumptionTransformer's behavior when get_assumptions is called before transformation.
        """
        at = AssumptionTransformer()
        control = clingo.Control()
        self.assertRaises(UntransformedException, lambda: at.get_assumption_literals(control))

    def test_assumption_transformer_get_assumptions_before_grounding(self) -> None:
        """
        Test the AssumptionTransformer's behavior when get_assumptions is called before transformation.
        """
        program_path = TEST_DIR.joinpath("res/test_program.lp")
        at = AssumptionTransformer()
        control = clingo.Control()
        at.parse_files([program_path])
        self.assertRaises(NotGroundedException, lambda: at.get_assumption_literals(control))

    def test_assumption_transformer_visit_definition(self) -> None:
        """
        Test the AssumptionTransformer's detection of constant definitions.
        """
        program_path = TEST_DIR.joinpath("res/test_program_constants.lp")
        at = AssumptionTransformer()
        control = clingo.Control()
        result = at.parse_files([program_path])
        control.add("base", [], result)
        control.ground([("base", [])])
        self.assertEqual(
            at.program_constants,
            {k: clingo.parse_term(v) for k, v in {"number": "42", "message": "helloworld"}.items()},
        )

    # RULE ID TRANSFORMER

    def test_rule_id_transformer(self) -> None:
        """
        Test the RuleIDTransformer's `parse_file` and `get_assumptions` methods.
        """
        program_path = TEST_DIR.joinpath("res/test_program.lp")
        program_path_transformed = TEST_DIR.joinpath("res/transformed_program_rule_ids.lp")
        rt = RuleIDTransformer()
        result = rt.parse_file(program_path)
        self.assertEqual(result.strip(), read_file(program_path_transformed).strip())
        assumptions = {
            (clingo.parse_term(s), True)
            for s in [
                "_rule(1)",
                "_rule(2)",
                "_rule(3)",
                "_rule(4)",
                "_rule(5)",
                "_rule(6)",
                "_rule(7)",
            ]
        }
        self.assertEqual(assumptions, rt.get_assumptions())

    # CONSTRAINT TRANSFORMER

    def test_constraint_transformer(self) -> None:
        """
        Test the ConstraintTransformer's `parse_file` method.
        """
        program_path = TEST_DIR.joinpath("res/test_program_constraints.lp")
        program_path_transformed = TEST_DIR.joinpath("res/transformed_program_constraints.lp")
        ct = ConstraintTransformer(constraint_head_symbol="unsat")
        result = ct.parse_files([program_path])
        self.assertEqual(result.strip(), read_file(program_path_transformed).strip())

    def test_constraint_transformer_include_id(self) -> None:
        """
        Test the ConstraintTransformer's `parse_file` method.
        """
        program_path = TEST_DIR.joinpath("res/test_program_constraints.lp")
        program_path_transformed = TEST_DIR.joinpath("res/transformed_program_constraints_id.lp")
        ct = ConstraintTransformer(constraint_head_symbol="unsat", include_id=True)
        with open(program_path, "r", encoding="utf-8") as f:
            result = ct.parse_string(f.read())
        self.assertEqual(result.strip(), read_file(program_path_transformed).strip())

    # RULE SPLITTER

    def test_rule_splitter(self) -> None:
        """
        Test the RuleSplitter's `parse_file` method.
        """

        program_path = TEST_DIR.joinpath("res/test_program_rules.lp")
        program_path_transformed = TEST_DIR.joinpath("res/transformed_program_rules_split.lp")
        rs = RuleSplitter()
        result = rs.parse_file(program_path)
        self.assertEqual(result.strip(), read_file(program_path_transformed).strip())

    # OPTIMIZATION REMOVER

    def test_optimization_remover(self) -> None:
        """
        Test the OptimizationRemover's `parse_file` and `parse_string_method` method.
        """

        program_path = TEST_DIR.joinpath("res/test_program_optimization.lp")
        program_path_transformed = TEST_DIR.joinpath("res/transformed_program_optimization.lp")
        optrm = OptimizationRemover()
        result_files = optrm.parse_files([program_path])
        with open(program_path, "r", encoding="utf-8") as f:
            result_string = optrm.parse_string(f.read())
        self.assertEqual(result_files.strip(), read_file(program_path_transformed).strip())
        self.assertEqual(result_files.strip(), result_string.strip())

    # FACT TRANSFORMER

    def test_fact_transformer(self) -> None:
        """
        Test the FactTransformer's `parse_files` and `parse_string_method` method.
        """

        program_path = TEST_DIR.joinpath("res/test_program.lp")
        program_path_transformed = TEST_DIR.joinpath("res/transformed_program_facts.lp")
        ft = FactTransformer(signatures={("a", 1), ("d", 1), ("e", 1)})
        result_files = ft.parse_files([program_path])
        with open(program_path, "r", encoding="utf-8") as f:
            result_string = ft.parse_string(f.read())
        self.assertEqual(result_files.strip(), read_file(program_path_transformed).strip())
        self.assertEqual(result_files.strip(), result_string.strip())
