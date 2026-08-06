import random

from clingexplaid.mus import CoreComputer
from clingexplaid.preprocessors import AssumptionPreprocessor, FilterSignature

n_assumptions = 500
core_size_ratio = 0.01
random_core = random.choices(range(1, n_assumptions), k=int(n_assumptions * core_size_ratio))
program = f"""
            a(1..{n_assumptions}).
            :- {", ".join([f"a({i})" for i in random_core])}.
            """
ap = AssumptionPreprocessor(filters={FilterSignature("a", 1)})
t = ap.process(program)
ap.control.ground([("base", [])])
cc = CoreComputer(ap.control, ap.assumptions)


def shrink_on_core(core) -> None:
    mus_literals = cc.shrink(core)
    print("MUS:", cc.mus_to_string(mus_literals))


_ = ap.control.solve(assumptions=list(ap.assumptions), on_core=shrink_on_core)
