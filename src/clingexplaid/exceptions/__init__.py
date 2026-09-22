"""Exceptions for Clingo-Explaid."""


class UnprocessedException(Exception):
    """
    The assumptions property of an AssumptionPreprocessor was called before the program was processed.
    """
