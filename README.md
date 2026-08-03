from clingexplaid.transformers.transformer_assumption import FilterSignature

# clingexplaid

API to aid the development of explanation systems using clingo

## Installation

<!-- --8<-- [start:installation] -->

Clingo-Explaid easily be installed with `pip`:

```bash
pip install clingexplaid
```

<!-- --8<-- [end:installation] -->

### Requirements

<!-- --8<-- [start:requirements] -->

- `python >= 3.10`
- `clingo >= 5.7.1`

<!-- --8<-- [end:requirements] -->

### Building from Source

Please refer to [DEVELOPEMENT](DEVELOPMENT.md)

## API

The following Examples show use-cases for using `clingexplaid`'s API.

### Minimal Unsatisfiable Subsets (MUS)

Transforming facts to Assumptions (necessary pre-processing step):

<!-- --8<-- [start:example-assumption-trasformer] -->

```python
from clingexplaid.preprocessors import AssumptionPreprocessor
from clingexplaid.preprocessors import (
    FilterSignature,
    FilterPattern,
)

PROGRAM = """
a(book;magazine;video).
b(test).
c(1..10).
d(1..3).
"""

ap = AssumptionPreprocessor(filters=[
    FilterSignature("a", 1),
    FilterPattern("d(2)")
])
result = ap.process(PROGRAM)
# You can either use the return value of `ap.process`
print(result)
# Or use `ap.control` with your transformed program already added
print(ap.control)
```

<!-- --8<-- [end:example-assumption-trasformer] -->

You can also use an existing control and pass it to the
`AssumptionPreprocessor` as follows:

<!-- --8<-- [start:example-assumption-trasformer-control] -->

```python
import clingo
from clingexplaid.preprocessors import AssumptionPreprocessor, FilterSignature, FilterPattern

FILE = "local/encoding.lp"

ctl = clingo.Control("0")
ap = AssumptionPreprocessor(
    control=ctl,
    filters=[
    FilterSignature("a", 1),
    FilterPattern("d(2)")
])
ap.process_files([FILE])

# The transformed files are added to ctl so it can be directly used
ctl.ground([("base", [])])
ctl.solve()
```

<!-- --8<-- [end:example-assumption-trasformer-control] -->

Getting a single MUS:

<!-- --8<-- [start:example-single-mus] -->

```python
from clingexplaid.preprocessors import AssumptionPreprocessor, FilterSignature
from clingexplaid.mus import CoreComputer

PROGRAM = """
a(1..3).
{b(4..6)}.

a(X) :- b(X).

:- a(X), X>=3.
"""

ap = AssumptionPreprocessor(filters={FilterSignature("a", 1)})
ap.process(PROGRAM)
ap.control.ground([("base", [])])
cc = CoreComputer(ap.control, ap.assumptions)

def shrink_on_core(core) -> None:
    mus_literals = cc.shrink(core)
    print("MUS:", cc.mus_to_string(mus_literals))

ap.control.solve(
    assumptions=list(ap.assumptions),
    on_core=shrink_on_core
)
```

<!-- --8<-- [end:example-single-mus] -->

Getting multiple MUS:

<!-- --8<-- [start:example-multi-mus] -->

```python
from clingexplaid.preprocessors import AssumptionPreprocessor
from clingexplaid.mus import CoreComputer

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
```

<!-- --8<-- [end:example-multi-mus] -->

### Unsatisfiable Constraints

<!-- --8<-- [start:example-unsat] -->

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
