"""
Tests for the preprocessors package
"""

from unittest import TestCase

import clingo

from clingexplaid.exceptions import UnprocessedException
from clingexplaid.preprocessors import AssumptionPreprocessor, FilterPattern, FilterSignature

from .test_main import TEST_DIR, read_file


class TestPreprocessors(TestCase):
    """
    Test cases for preprocessors.
    """

    # ASSUMPTION PREPROCESSOR

    def test_assumption_preprocessor_parse_file(self) -> None:
        """
        Test the AssumptionPreprocessor's `parse_file` method.
        """
        program_path = TEST_DIR.joinpath("res/test_program.lp")
        program_path_transformed = TEST_DIR.joinpath("res/transformed_program_assumptions_certain_signatures.lp")
        filters = [FilterSignature(c, 1) for c in "abcdef"]
        ap = AssumptionPreprocessor(filters=filters)
        with open(program_path, "r", encoding="utf-8") as file:
            result = ap.process(file.read())
        self.assertEqual(result.strip(), read_file(program_path_transformed).strip())

    def test_assumption_preprocessor_parse_file_no_signatures(self) -> None:
        """
        Test the AssumptionPreprocessor's `parse_file` method with no signatures provided.
        """
        program_path = TEST_DIR.joinpath("res/test_program.lp")
        program_path_transformed = TEST_DIR.joinpath("res/transformed_program_assumptions_all.lp")
        ap = AssumptionPreprocessor()
        with open(program_path, "r", encoding="utf-8") as file:
            result = ap.process(file.read())
        self.assertEqual(result.strip(), read_file(program_path_transformed).strip())

    def test_assumption_preprocessor_parse_nothing(self) -> None:
        """
        Test the AssumptionPreprocessor's `process` method with an empty filters list.
        """
        program_path = TEST_DIR.joinpath("res/test_program.lp")
        program_path_transformed = TEST_DIR.joinpath("res/transformed_program_nothing_transformed.lp")
        ap = AssumptionPreprocessor(filters=[])
        with open(program_path, "r", encoding="utf-8") as file:
            result = ap.process(file.read())
        self.assertEqual(result.strip(), read_file(program_path_transformed).strip())

    def test_assumption_preprocessor_parse_pattern_filter(self) -> None:
        """
        Test the AssumptionPreprocessor's `parse_file` method with no signatures provided.
        """
        program_path = TEST_DIR.joinpath("res/test_program_pattern.lp")
        program_path_transformed = TEST_DIR.joinpath("res/transformed_program_pattern.lp")
        filters = {FilterPattern("a(_,value,_)")}
        ap = AssumptionPreprocessor(filters=filters)
        with open(program_path, "r", encoding="utf-8") as file:
            result = ap.process(file.read())
        self.assertEqual(result.strip(), read_file(program_path_transformed).strip())

    def test_assumption_preprocessor_get_assumptions_before_transformation(self) -> None:
        """
        Test the AssumptionPreprocessor's behavior when get_assumptions is called before transformation.
        """
        ap = AssumptionPreprocessor()
        self.assertRaises(UnprocessedException, lambda: ap.assumptions)

    def test_assumption_preprocessor_visit_definition(self) -> None:
        """
        Test the AssumptionPreprocessor's detection of constant definitions.
        """
        program_path = TEST_DIR.joinpath("res/test_program_constants.lp")
        ap = AssumptionPreprocessor()
        with open(program_path, "r", encoding="utf-8") as file:
            result = ap.process(file.read())
        ap.control.add("base", [], result)
        ap.control.ground([("base", [])])
        self.assertEqual(
            ap.constants,
            {k: clingo.parse_term(v) for k, v in {"number": "42", "message": "helloworld"}.items()},
        )

    def test_assumption_preprocessor_parse_files(self) -> None:
        """Test the AssumptionPreprocessor's `parse_files` method."""

        program_path = TEST_DIR.joinpath("res/test_includes.lp")
        program_path_transformed = TEST_DIR.joinpath("res/transformed_includes.lp")
        ap = AssumptionPreprocessor()
        result = ap.process_files([str(program_path)])
        self.assertEqual(result.strip(), read_file(program_path_transformed).strip())

    def test_assumption_preprocessor_parse_files_none(self) -> None:
        """Test the AssumptionPreprocessor's `parse_files` method on files=None"""

        ap = AssumptionPreprocessor()
        result = ap.process_files()
        self.assertEqual(result.strip(), "")

    def test_assumption_preprocessor_with_constant(self) -> None:
        """Test the AssumptionPreprocessor's `parse_files` method on with a constant definition in the program"""

        program_path = TEST_DIR.joinpath("res/test_constant.lp")
        program_path_transformed = TEST_DIR.joinpath("res/transformed_constant.lp")
        ap = AssumptionPreprocessor()
        result = ap.process_files([str(program_path)])
        self.assertEqual(result.strip(), read_file(program_path_transformed).strip())
