from clingexplaid.mus import CoreComputer
from clingexplaid.preprocessors import AssumptionPreprocessor, FilterSignature


def read_files(paths: list[str]) -> str:
    return "\n".join([open(p, "r").read() for p in paths])


ap = AssumptionPreprocessor(filters={FilterSignature("edge", 2)})
t = ap.process(
    read_files(
        [
            "examples/performance/mus.lp",
            "examples/performance/mid.lp",
        ]
    )
)

ap.control.ground([("base", [])])
cc = CoreComputer(ap.control, ap.assumptions)


def shrink_on_core(core) -> None:
    mus_literals = cc.shrink(core)
    print("MUS:", cc.mus_to_string(mus_literals))


_ = ap.control.solve(assumptions=list(ap.assumptions), on_core=shrink_on_core)
