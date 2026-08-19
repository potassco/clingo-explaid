from clingexplaid.mus import SubsetComputer
from clingexplaid.mus.sets import MaximalSatisfiableSubset, MinimalCorrectionSet, MinimalUnsatisfiableSubset

from clingexplaid.preprocessors import AssumptionPreprocessor

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
