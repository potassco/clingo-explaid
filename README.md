# clingexplaid

> [!CAUTION] This version uses a local dependency of `musclingo` for
> development purposes. This should be fixed before it is released!

API to aid the development of explanation systems using clingo

## Installation

Clingo-Explaid easily be installed with `pip`:

```bash
pip install clingexplaid
```

### Requirements

- `python >= 3.11`
- `clingo >= 5.7.1`

### Building from Source

Please refer to [DEVELOPEMENT](DEVELOPMENT.md)

## API Usage

The following Examples show use-cases for `clingexplaid`'s API.

### Unsatisfiable Functionality

#### Pre-Processing

Transforming facts to Assumptions (necessary pre-processing step):

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

You can also use an existing control and pass it to the
`AssumptionPreprocessor` as follows:

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
    ]
)
ap.process_files([FILE])

# The transformed files are added to ctl so it can be directly used
ctl.ground([("base", [])])
ctl.solve()
```

#### Computing relevant subsets (MUS, MSS, MCS)

Getting a single MUS:

```python
from clingexplaid.preprocessors import AssumptionPreprocessor, FilterSignature
from clingexplaid.unsat import SubsetComputer

PROGRAM = """
a(1..3).
{b(4..6)}.

a(X) :- b(X).

:- a(X), X>=3.
"""

ap = AssumptionPreprocessor(filters={FilterSignature("a", 1)})
ap.process(PROGRAM)
ap.control.ground([("base", [])])
sc = SubsetComputer(ap.control, ap.assumptions)

def shrink_on_core(core) -> None:
    mus = sc.mus(core)
    print(mus)

ap.control.solve(
    assumptions=list(ap.assumptions),
    on_core=shrink_on_core
)
```

Getting multiple MUS:

```python
from clingexplaid.preprocessors import AssumptionPreprocessor
from clingexplaid.unsat import SubsetComputer

PROGRAM = """
a(1..3).
b(1..3).

:- a(X), b(X).
"""

ap = AssumptionPreprocessor()
ap.process(PROGRAM)
ap.control.ground([("base", [])])
sc = SubsetComputer(ap.control, ap.assumptions)

for i, mus in enumerate(sc.multiple()):
    print(f"{i}:", mus)
```

Getting multiple relevant subsets (MUS, MSS, and MCS):

```python
from clingexplaid.preprocessors import AssumptionPreprocessor
from clingexplaid.unsat import SubsetComputer
from clingexplaid.unsat.sets import [
    MinimalUnsatisfiableSubset,
    MaximalSatisfiableSubset,
    MinimalCorrectionSet
]

PROGRAM = """
a(1..3).
b(1..3).

:- a(X), b(X).
"""

ap = AssumptionPreprocessor()
ap.process(PROGRAM)
ap.control.ground([("base", [])])
sc = SubsetComputer(ap.control, ap.assumptions)

types = [MinimalUnsatisfiableSubset, MaximalSatisfiableSubset, MinimalCorrectionSet]
for i, subset in enumerate(sc.multiple(types)):
    print(f"{i}:", subset)
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
