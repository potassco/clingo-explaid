import time

from clingexplaid.mus import CoreComputer
from clingexplaid.preprocessors import AssumptionPreprocessor, FilterSignature

PROGRAM = """
a(1..3).
{b(4..6)}.

a(X) :- b(X).

:- a(X), X>=3.
"""

start_t = time.perf_counter()
ap = AssumptionPreprocessor(filters={FilterSignature("a", 1)})
ap.process(PROGRAM)
ap.control.ground([("base", [])])
cc = CoreComputer(ap.control, ap.assumptions)


def shrink_on_core(core) -> None:
    mus_literals = cc.shrink(core)
    print("MUS:", cc.mus_to_string(mus_literals))


ap.control.solve(assumptions=list(ap.assumptions), on_core=shrink_on_core)
end_t = time.perf_counter()

print(f"Time: {end_t - start_t}")
