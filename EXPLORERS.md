# Explorers

This document contains some intuition for the new `Explorer` classes in
`clingoexplaid`.

### ASP Explorer

#### Approach

> **Example** Program $\\Pi$ : `UNSAT` Assumptions $A$: `+a`, `+b`, `+c`, `+d`
> MUS: `{a,b}`, `{b,d}`

> \[!NOTE\]
>
> Example Search Space
>
> | Subset      | Type     |
> | :---------- | :------- |
> | `{}`        | `🟢 SAT` |
> | `{a}`       | `🟢 SAT` |
> | `{b}`       | `🟢 SAT` |
> | `{c}`       | `🟢 SAT` |
> | `{d}`       | `🟢 SAT` |
> | `{a,b}`     | `🔴 MUS` |
> | `{a,c}`     | `🟢 SAT` |
> | `{a,d}`     | `🟢 SAT` |
> | `{b,c}`     | `🟢 SAT` |
> | `{b,d}`     | `🔴 MUS` |
> | `{c,d}`     | `🟢 SAT` |
> | `{a,b,c}`   | `🔴 US`  |
> | `{a,b,d}`   | `🔴 US`  |
> | `{b,c,d}`   | `🔴 US`  |
> | `{a,c,d}`   | `🟢 SAT` |
> | `{a,b,c,d}` | `🔴 US`  |

For the explored check and finding the next suitable subset candidates an ASP
exploration encoding is used

> \[!NOTE\]
>
> Example for the Exploration Encoding
>
> ```asp
> 1{_unsat; _sat}.  % Satisfiability indicators
> {a;b;c;d}.      % Assumption choices
> ```

##### Enumerating MUS Candidates

When the iterative deletion algorithm (ID) is called on the full assumption
set, the following subsets are checked in the listed order:

1. `🔴 UNSAT` : `{a,b,c,d}`
   - No constraint added
1. `🔴 UNSAT` : `{b,c,d}`
   - No constraint added
1. `🟢 SAT` : `{c,d}`
   - Constraint added: `:- not a, not b, _sat.`
1. `🟢 SAT` : `{b}` (working set)
   - Constraint added: `:- not a, not c, not d, _sat.`
1. `🔴 UNSAT` : `{d} ∪ {b}`
   - No constraint added
1. `🟢 SAT` : `{} ∪ {b}`
   - Constraint added: `:- not a, not c, not d, _sat.` (duplicate)

- MUS found : `{b,d}`
  - Constraint added: `:- b, d, _unsat.`

Now after finding the first MUS with the ID algorithm, the updated $\\Pi$ with
the new constraints is solved using `clingo` and the first answer set is taken
as the next MUS candidate. For getting only the valid next possible candidates
`_unsat` and `_sat` are both assumed `True`.

##### Checking the explored Status

The same `clingo.Control` object with the updated exploration encoding from
\[\[#Enumerating MUS Candidates\]\] is used to check whether a provided subset
$S$ is either `unexplored`, `explored(sat)`, or `explored(unsat)`.

For that, all assumptions of the subset are assumed, while also the assumptions
missing from the subset ($A\\setminus S$) are assumed as negated.

> \[!NOTE\]
>
> Example Assumptions
>
> For the subset `{a,c,d}` we would assume `(a,True)`, `(b,False)`, `(c,True)`,
> and `(d,True)`.

Then `clingo` is called and all models are returned. Now one of three cases
holds:

1. 1 Model, with `_sat` included
   - This indicates that the subset is already **explored** and
     **unsatisfiable**
1. 1 Model, with `_unsat` included
   - This indicates that the subset is already **explored** and **satisfiable**
1. 3 Models
   - This indicates that the subset is not explored yet and a valid next
     candidate
