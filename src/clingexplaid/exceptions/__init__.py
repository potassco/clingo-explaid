"""Exceptions for ClingExplaid"""


class UnprocessedException(Exception):
    """
    Exception raised if the assumptions property of an AssumptionPreprocessor is called before it is used to
    preprocess a program.
    """
