import clingo

from clingexplaid.utils import get_solver_literal_lookup
from clingexplaid.utils.transformer import AssumptionTransformer


sig = [
    ('dog', 1),
    ('mantis', 1),
    ('axolotl', 1),
    ('something_true', 0),
    ('snake', 1),
]

at = AssumptionTransformer(sig)

files = ["test/instance.lp", "test/encoding.lp"]

ctl = clingo.Control()

transformed_program = ""

for f in files:
    transformed_program += at.parse_file(f) + "\n"

ctl.add("base", [], transformed_program)

ctl.ground([("base", [])])

literal_lookup = get_solver_literal_lookup(ctl)

assumptions = at.get_assumptions(ctl)
print(assumptions, [str(literal_lookup[a]) for a in assumptions])

# uncore_shirker = UCORE(ctl, assumtions)
#
# ctl.solve(assumptions=assumtions,on_core=uncore_shirker.get_minimal)
# m_core = uncore_shirker.minimal
