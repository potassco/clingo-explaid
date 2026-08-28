"""Test script to enumerate one MUS of a program."""

import time
from collections.abc import Sequence

from clingexplaid.preprocessors import AssumptionPreprocessor, FilterSignature
from clingexplaid.unsat import SubsetComputer

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


def _shrink_on_core(core: Sequence[int]) -> None:
    mus = sc.mus(core)
    print(mus)


ap.control.solve(assumptions=list(ap.assumptions), on_core=_shrink_on_core)
end_t = time.perf_counter()

print(f"Time: {end_t - start_t}")
