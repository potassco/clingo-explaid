"""Test script to enumerate all elevant subsets of a program."""

from clingexplaid.preprocessors import AssumptionPreprocessor
from clingexplaid.unsat import SubsetComputer
from clingexplaid.unsat.sets import MaximalSatisfiableSubset, MinimalCorrectionSet, MinimalUnsatisfiableSubset

PROGRAM = """
a(1..3).
b(1..3).

:- a(X), b(X).
"""

ap = AssumptionPreprocessor()
ap.process(PROGRAM)
ap.control.ground([("base", [])])
sc = SubsetComputer(ap.control, ap.assumptions)

mus_generator = sc.multiple(types={MaximalSatisfiableSubset, MinimalCorrectionSet, MinimalUnsatisfiableSubset})
for i, mus in enumerate(mus_generator):
    print(f"{i}:", mus)
