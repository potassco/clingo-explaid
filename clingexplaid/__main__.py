# import time
#
# import clingo
#
# from clingexplaid.utils import get_solver_literal_lookup
# from clingexplaid.utils.transformer import AssumptionTransformer
# from clingexplaid.utils.muc import CoreComputer
#
#
# sig = [
#     ('dog', 1),
#     ('mantis', 1),
#     ('axolotl', 1),
#     ('something_true', 0),
#     ('snake', 1),
#     ('test', 0)
# ]
#
# at = AssumptionTransformer(sig)
#
# files = ["temp/instance.lp", "temp/encoding.lp"]
#
# ctl = clingo.Control()
#
# transformed_program = ""
#
# for f in files:
#     transformed_program += at.parse_file(f) + "\n"
#
# ctl.add("base", [], transformed_program)
#
# ctl.ground([("base", [])])
#
# literal_lookup = get_solver_literal_lookup(ctl)
#
# assumptions = at.get_assumptions(ctl)
# print(assumptions, [str(literal_lookup[a]) for a in assumptions])
#
# cc = CoreComputer(ctl, assumptions)
#
# ctl.solve(assumptions=list(assumptions), on_core=cc.shrink)
# print(cc.minimal)
