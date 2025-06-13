"""
Tests for the utils package
"""

from typing import List
from unittest import TestCase

import clingo
from clingo.ast import parse_string

from clingexplaid.utils import get_constant_string, get_constants_from_arguments, get_signatures_from_model_string
from clingexplaid.utils.symbols import ast_symbolic_atom_to_symbol


class TestUtils(TestCase):
    """
    Test cases for clingexplaid.
    """

    def test_get_signatures_from_model_string(self) -> None:
        """
        Test getting signatures from a model string.
        """
        model_string = "a(1,2) a(1,5) a(3,5) a(1,2,3) a(1,3,5), foo(bar), zero"
        signatures = get_signatures_from_model_string(model_string)
        self.assertEqual(signatures, {("a", 2), ("a", 3), ("foo", 1), ("zero", 0)})

    def test_get_constants_from_arguments(self) -> None:
        """
        Test getting constants from argument vector.
        """
        self.assertEqual(get_constants_from_arguments(["-c", "a=42"]), {"a": "42"})
        self.assertEqual(get_constants_from_arguments(["test/dir/file.lp", "--const", "blob=value"]), {"blob": "value"})
        self.assertEqual(get_constants_from_arguments(["--const", "-a", "test/42"]), {})

    def test_get_constant_strings(self) -> None:
        """
        Test getting constant strings
        """
        self.assertEqual(get_constant_string("test", "42"), "test=42")
        self.assertEqual(get_constant_string("name", "value"), "name=value")
        with self.assertRaises(ValueError):
            get_constant_string("123", "value")
        self.assertEqual(get_constant_string("name", "123", prefix="#const "), "#const name=123")
        self.assertEqual(get_constant_string("name", "123", prefix="-c "), "-c name=123")

    def test_ast_to_symbol(self) -> None:
        """
        Test converting an AST to a symbol.
        """
        ast_list: List[clingo.ast.AST] = []
        parse_string(
            """
            test(1).
            atom.
            variables(1,2,3,4,5).
        """,
            ast_list.append,
        )
        results = [
            clingo.parse_term("test(1)"),
            clingo.parse_term("atom"),
            clingo.parse_term("variables(1,2,3,4,5)"),
        ]

        for ast, result in zip([a for a in ast_list if a.ast_type == clingo.ast.ASTType.Rule], results):
            self.assertEqual(ast_symbolic_atom_to_symbol(ast.head), result)
