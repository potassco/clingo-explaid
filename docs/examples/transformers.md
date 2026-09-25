---
title: "Transformers : Examples"
icon: "material/cog"
---

# Transformers

These examples highlight how to use `clingexplaid`'s transformers.
A transformer rewrites an ASP program on the level of its abstract syntax tree (AST).
Every transformer offers a `parse_string` method that takes a program as a string and returns the transformed program as a string.
To transform files instead, use `parse_files` or `parse_file`, depending on the transformer.

!!! note
    The transformed programs start with `#program base.`, since clingo's parser adds this statement to every program.

## `ConstraintTransformer`

The [`ConstraintTransformer`](../../reference/api/transformers#clingexplaid.transformers.ConstraintTransformer) adds an atom to the head of every integrity constraint.
Instead of making the program unsatisfiable, a firing constraint now derives this atom, which tells you which constraint was violated.

```python
from clingexplaid.transformers import ConstraintTransformer

PROGRAM = """
a(1..3).
:- a(X), X > 2.
"""

ct = ConstraintTransformer("unsat")
print(ct.parse_string(PROGRAM))
```

<div class="grid" markdown>

```clingo title="Original program"
a(1..3).
:- a(X), X > 2.
```

```clingo title="Transformed program"
#program base.
a((1..3)).
unsat :- a(X); X > 2.
```

</div>

With `include_id=True`, each constraint gets its own numbered atom, so you can tell the constraints apart.
The location of every constraint in the original program is stored in `ct.constraint_location_lookup`, indexed by its number.

```python
from clingexplaid.transformers import ConstraintTransformer

PROGRAM = """
a(1..3).
:- a(X), X > 2.
:- not a(4).
"""

ct = ConstraintTransformer("unsat", include_id=True)
print(ct.parse_string(PROGRAM))
```

<div class="grid" markdown>

```clingo title="Original program"
a(1..3).
:- a(X), X > 2.
:- not a(4).
```

```clingo title="Transformed program"
#program base.
a((1..3)).
unsat(1) :- a(X); X > 2.
unsat(2) :- not a(4).
```

</div>

## `FactTransformer`

The [`FactTransformer`](../../reference/api/transformers#clingexplaid.transformers.FactTransformer) removes facts from a program.
Without arguments, it removes all facts.

```python
from clingexplaid.transformers import FactTransformer

PROGRAM = """
a(1).
b(2).
c(X) :- a(X).
"""

ft = FactTransformer()
print(ft.parse_string(PROGRAM))
```

<div class="grid" markdown>

```clingo title="Original program"
a(1).
b(2).
c(X) :- a(X).
```

```clingo title="Transformed program"
#program base.
c(X) :- a(X).
```

</div>

To remove only some facts, pass a set of signatures as `(name, arity)` tuples.
Facts with any other signature are kept.

```python
from clingexplaid.transformers import FactTransformer

PROGRAM = """
a(1).
b(2).
c(X) :- a(X).
"""

ft = FactTransformer(signatures={("a", 1)})
print(ft.parse_string(PROGRAM))
```

<div class="grid" markdown>

```clingo title="Original program"
a(1).
b(2).
c(X) :- a(X).
```

```clingo title="Transformed program"
#program base.
b(2).
c(X) :- a(X).
```

</div>

## `OptimizationRemover`

The [`OptimizationRemover`](../../reference/api/transformers#clingexplaid.transformers.OptimizationRemover) removes all optimization statements from a program.
This covers `#minimize` and `#maximize` statements as well as weak constraints.

```python
from clingexplaid.transformers import OptimizationRemover

PROGRAM = """
{ a(1..3) }.
#minimize { X : a(X) }.
:~ a(2). [1@1]
"""

opt = OptimizationRemover()
print(opt.parse_string(PROGRAM))
```

<div class="grid" markdown>

```clingo title="Original program"
{ a(1..3) }.
#minimize { X : a(X) }.
:~ a(2). [1@1]
```

```clingo title="Transformed program"
#program base.
{ a((1..3)) }.
```

</div>

## `RuleIDTransformer`

The [`RuleIDTransformer`](../../reference/api/transformers#clingexplaid.transformers.RuleIDTransformer) adds a numbered `_rule` atom to the body of every rule.
This keeps each ground rule traceable to the rule it came from.
A choice rule over all `_rule` atoms is added at the end, so they don't change the program's answer sets.
`get_assumptions` returns the assumptions that set all `_rule` atoms to true.

```python
from clingexplaid.transformers import RuleIDTransformer

PROGRAM = """
a(1).
b(X) :- a(X).
:- b(1).
"""

rt = RuleIDTransformer()
print(rt.parse_string(PROGRAM))

# Assumptions setting _rule(1), _rule(2) and _rule(3) to true
assumptions = rt.get_assumptions()
```

<div class="grid" markdown>

```clingo title="Original program"
a(1).
b(X) :- a(X).
:- b(1).
```

```clingo title="Transformed program"
#program base.
a(1) :- _rule(1).
b(X) :- a(X); _rule(2).
#false :- b(1); _rule(3).
{_rule(1..3)}. % Choice rule to allow all _rule atoms to become assumptions
```

</div>

## `RuleSplitter`

The [`RuleSplitter`](../../reference/api/transformers#clingexplaid.transformers.RuleSplitter) splits every rule with a body into two rules.
The first rule derives a `_body` atom from the original body.
Its arguments are the body encoded in base64 and a tuple of the body's variables.
The second rule derives the original head from this `_body` atom.
In the example, `YShYKQ==` is the base64 encoding of `a(X)`.

```python
from clingexplaid.transformers import RuleSplitter

PROGRAM = """
a(1).
b(X) :- a(X).
"""

rs = RuleSplitter()
print(rs.parse_string(PROGRAM))
```

<div class="grid" markdown>

```clingo title="Original program"
a(1).
b(X) :- a(X).
```

```clingo title="Transformed program"
#program base.
a(1).
_body("YShYKQ==",(X,)) :- a(X).
b(X) :- _body("YShYKQ==",(X,)).
```

</div>
