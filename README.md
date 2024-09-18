# clingexplaid

Tools to aid the development of explanation systems using clingo

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

## Usage

Run the following for basic usage information:

```bash
clingexplaid -h
```

### Interactive Mode

We provide an interactive terminal user interface (textual) where all modes are
accessible in an interactive format. You can start this mode by using the
command below.

```bash
clingexplaid <files> --interactive
```

#### Example: MUS Sudoku

Below is one Example call using our [Sudoku Example](examples/sudoku).

```bash
clingexplaid examples/sudoku/encoding.lp examples/sudoku/instance.lp --interactive
```

![](example_mus.png)

#### Example: Show Decisions

This Example shows the interactive Solver Decision Tree generated from
[`examples/misc/sat_simple.lp`](examples/misc/sat_simple.lp).

![](example_show_decisions.png)

### Clingo Application Class

The clingexplaid CLI (based on the `clingo.Application` class) extends clingo
with `<method>` and `<options>`.

```bash
clingexplaid <method> <options>
```

- `<method>`: specifies which Clingexplaid method is used (Required)
  - Options:
    - `--muc`:
      - Computes the Minimal Unsatisfiable Cores (MUCs) of the provided
        unsatisfiable program
    - `--unsat-constraints`:
      - Computes the Unsatisfiable Constraints of the unsatisfiable program
        provided.
    - `--show-decisions`:
      - Visualizes the decision process of clasp
- `<options>`: Additional options for the different methods
  - For `--muc`:
    - `-a`, `--assumption-signature`: limits which facts of the current program
      are converted to choices/assumptions for finding the MUCs (Default: all
      facts are converted)
  - For `--show-decisions`:
    - `--decision-signature`: limits which decisions are shown in the
      visualization (Default: all atom's decisions are shown)

### Examples

Given the simple program below [`simple.lp`](examples/misc/simple.lp) we want
to find the contained MUC (Minimal Unsatisfiable Core).

```
a(1..5).
b(5..10).

:- a(X), b(X).
```

For this we can call `clingexplaid` the following way:

```bash
clingexplaid examples/misc/simple.lp --muc 0
```

This converts all facts of the program to choices and assumptions and returns
the contained MUC from that.

```
MUC  1
b(5) a(5)
```

A selection of more examples can be found [here](examples)

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
