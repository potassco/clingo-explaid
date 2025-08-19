import os
import random
import re
from pathlib import Path
from typing import Set, Tuple

import clingo

MIN_ASSUMPTIONS = 1
MAX_ASSUMPTIONS = 100
MIN_MUS = 1
MAX_MUS = 10
OUT_DIR = Path(__file__).parent / "generated"
N_INSTANCES = 15


def print_mus(contains_atoms: Set[clingo.Symbol], mus_id: int, max_assumptions: int) -> None:
    symbols = [" " for _ in range(max_assumptions)]
    for a in contains_atoms:
        if a.arguments[0].number == mus_id:
            symbols[a.arguments[1].number - 1] = "X"
    print("[" + "".join(symbols) + "]")


def on_model(model: clingo.Model, max_assumptions: int) -> None:
    m_set = {a for a in model.symbols(atoms=True) if a.match("m", 1)}
    a_set = {a for a in model.symbols(atoms=True) if a.match("a", 1)}
    contains_set = {a for a in model.symbols(atoms=True) if a.match("contains", 2)}
    print(f"INSTANCE [mus_amount={len(m_set)}]")
    for mus in m_set:
        print_mus(contains_set, mus.arguments[0].number, max_assumptions)
    print("Storing Benchmark Instance")
    store_benchmark_instance(m_set, a_set, contains_set)
    print("Stored Benchmark Instance")


def compose_mus_constraint(mus_id: int, contains_set: Set[clingo.Symbol]) -> str:
    mus_assumption_ids = [a.arguments[1].number for a in contains_set if a.arguments[0].number == mus_id]
    mus_assumptions = [f"a({a_id})" for a_id in mus_assumption_ids]
    return ":- " + ", ".join(mus_assumptions) + ".\n"


def store_benchmark_instance(
    mus_set: Set[clingo.Symbol], assumption_set: Set[clingo.Symbol], contains_set: Set[clingo.Symbol]
) -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    filename_pattern = re.compile(r"^instance_.*\.lp$")
    matching_filenames = [f for f in os.listdir(OUT_DIR) if filename_pattern.match(f)]
    last_instance_number = (
        max([int(f.replace("instance_", "").replace(".lp", "")) for f in matching_filenames])
        if matching_filenames
        else 0
    )
    instance_number = last_instance_number + 1

    with open(OUT_DIR / f"instance_{instance_number}.lp", "w") as f:
        output_string = ""
        output_string += ". ".join([str(a) for a in assumption_set]) + ".\n"
        for mus in mus_set:
            output_string += compose_mus_constraint(mus.arguments[0].number, contains_set)
        f.write(output_string)


def get_random_parameters() -> Tuple[int, int, int, int]:
    assumptions = random.randint(MIN_ASSUMPTIONS, MAX_ASSUMPTIONS)
    mus = random.randint(MIN_MUS, MAX_MUS)
    min_mus_assumptions = random.randint(1, assumptions)
    max_mus_assumptions = random.randint(min_mus_assumptions, assumptions)
    return assumptions, mus, min_mus_assumptions, max_mus_assumptions


def compute_model():
    n_a, n_m, min_a, max_a = get_random_parameters()
    print(f"Computing for: [assumptions={n_a}, mus={n_m}, min_mus_assumptions={min_a}, max_mus_assumptions={max_a}]")
    constant_string = (
        f"#const min_assumptions={n_a}. "
        f"#const max_assumptions={n_a}. "
        f"#const min_mus={n_m}. "
        f"#const max_mus={n_m}. "
        f"#const min_mus_assumptions={min_a}. "
        f"#const max_mus_assumptions={max_a}."
    )
    ctl = clingo.Control()
    ctl.add("base", [], constant_string)
    ctl.load(str(Path(__file__).parent / "generator.lp"))
    print("Started Grounding")
    ctl.ground([("base", [])])
    print("Finished Grounding")
    # ctl.configuration.solve.models = 10
    # ctl.configuration.solver.rand_freq = 0.001251220762
    ctl.solve(on_model=lambda x: on_model(x, n_a), on_unsat=lambda x: print("UNSAT"), on_finish=lambda x: print("DONE"))


if __name__ == "__main__":
    for i in range(N_INSTANCES):
        compute_model()
