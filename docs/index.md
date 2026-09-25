---
hide:
  - navigation
  - toc
---

# clingexplaid

--8<-- "README.md:description"

Unsatisfiable programs in Answer Set Programming (ASP) can be challenging to debug or explain.
*clingexplaid* helps you find you to identify the core of that unsatisfiability, so you can debug encodings,
explain results to users, or build interactive explanation tools on top of [clingo](https://potassco.org/clingo/).

<div class="grid cards" markdown>

-   :material-rocket-launch: __Getting Started__

    ---

    Install *clingexplaid* and compute your first unsatisfiable subset in a
    few lines of Python.

    [:octicons-arrow-right-24: Quick Start Guide](use/quick-start.md)

-   :material-code-braces: __Examples__

    ---

    Practical examples for subsets, unsatisfiable constraints, pre-processors
    and transformers.

    [:octicons-arrow-right-24: See Examples](examples/index.md)

-   :material-book-open-variant: __Reference__

    ---

    Detailed API documentation of all modules, classes and functions.

    [:octicons-arrow-right-24: API Documentation](reference/index.md)

</div>

## What's inside

*clingexplaid* is structured as a set of building blocks that can be combined
freely:

-   **Pre-processors** turn selected facts of a program into *assumptions*.
    This is the necessary first step for every subset computation, since the
    solver can only reason about which assumptions cause a conflict.
    See [`clingexplaid.preprocessors`](reference/api/preprocessors.md).

-   **Subset computation** finds the relevant subsets of an unsatisfiable
    assumption set: *Minimal Unsatisfiable Subsets* (MUS), *Maximal
    Satisfiable Subsets* (MSS) and *Minimal Correction Sets* (MCS), either a
    single one or enumerated one after the other.
    See [`clingexplaid.unsat`](reference/api/unsat.md).

-   **Unsatisfiable constraints** identifies which integrity constraints of a
    program are violated and therefore responsible for unsatisfiability.
    See the [Unsatisfiable Constraints](examples/constraints.md) examples.

-   **Transformers** rewrite the abstract syntax tree of a program, for
    example to tag rules with identifiers, relax constraints or remove
    optimization statements.
    See [`clingexplaid.transformers`](reference/api/transformers.md).

-   **Propagators** hook into the solving process and record the order in
    which the solver makes its decisions, which helps to trace how a
    conflict arises.
    See [`clingexplaid.propagators`](reference/api/propagators.md).

## A first look

--8<-- "README.md:example-mus-multiple"

Every fact of the program is turned into an assumption, and the
`SubsetComputer` then enumerates all minimal sets of facts that cannot hold
together. Head over to the [Quick Start Guide](use/quick-start.md) for a
step-by-step introduction.

!!! info
    *clingexplaid* is part of the [Potassco](https://potassco.org) suite.
