from clingexplaid.mus import CoreComputer
from clingexplaid.preprocessors import AssumptionPreprocessor

PROGRAM = """
a(1..3).
b(1..3).

:- a(X), b(X).
"""

ap = AssumptionPreprocessor()
ap.process(PROGRAM)
ap.control.ground([("base", [])])
cc = CoreComputer(ap.control, ap.assumptions)

mus_generator = cc.get_multiple_minimal()
for i, mus in enumerate(mus_generator):
    print(f"MUS {i}:", cc.mus_to_string(mus))
