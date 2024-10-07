# clingexplaid

API to aid the development of explanation systems using clingo

## Installation

Clingo-Explaid easily be installed with `pip`:

```bash
pip install clingexplaid
```

### Requirements

- `python >= 3.9`
- `clingo >= 5.7.1`

### Building from Source

Please refer to [DEVELOPEMENT](DEVELOPMENT.md)

## API

Here are two example for using `clingexplaid`'s API.

### Minimal Unsatisfiable Subsets (MUS)

```python
import clingo
from clingexplaid.transformers import AssumptionTransformer
from clingexplaid.mus import CoreComputer

PROGRAM = """
a(1..3).
{b(4..6)}.

a(X) :- b(X).

:- a(X), X>=3.
"""

control = clingo.Control()
at = AssumptionTransformer(signatures={("a", 1)})

transformed_program = at.parse_string(PROGRAM)

control.add("base", [], transformed_program)
control.ground([("base", [])])

assumptions = at.get_assumption_literals(control)

cc = CoreComputer(control, assumptions)


def shrink_on_core(core) -> None:
    mus_literals = cc.shrink(core)
    print("MUS:", cc.mus_to_string(mus_literals))


control.solve(assumptions=list(assumptions), on_core=shrink_on_core)
```

### Unsatisfiable Constraints

```python
from clingexplaid.unsat_constraints import UnsatConstraintComputer

PROGRAM = """
a(1..3).
{b(4..6)}.

a(X) :- b(X).

:- a(X), X>=3.
"""

ucc = UnsatConstraintComputer()
ucc.parse_string(PROGRAM)
unsat_constraints = ucc.get_unsat_constraints()

for uc_id, unsat_constraint in unsat_constraints.items():
    print(f"Unsat Constraint {uc_id}:", unsat_constraint)
```
