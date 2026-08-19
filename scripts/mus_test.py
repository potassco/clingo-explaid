import time

from clingexplaid.mus import SubsetComputer
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
sc = SubsetComputer(ap.control, ap.assumptions)


def shrink_on_core(core) -> None:
    mus = sc.mus(core)
    print(mus)


ap.control.solve(assumptions=list(ap.assumptions), on_core=shrink_on_core)
end_t = time.perf_counter()

print(f"Time: {end_t - start_t}")
