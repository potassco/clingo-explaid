# clingexplaid

This project template is configured to ease collaboration. Linters, formatters,
and actions are already configured and ready to use.

To use the project template, run the `init.py` script to give the project a
name and some metadata. The script can then be removed afterward and the
`setup.cfg` file adjusted.

## Installation

```shell
pip install clingexplaid
```

## Usage

```bash
clingexplaid -h
```

Compute Minimal Unsatisfiable Core from unsatisfiable program:

```bash
clingexplaid <filenames> --assumption-signature signature/arity
```

+ `--assumption-signature` is optional to allow for only specific facts to be transformed to assumptions
	+ if no such option is given all facts are transformed to assumptions regardless of their signature

## Development

To improve code quality, we run linters, type checkers, and unit tests. The
tools can be run using [nox]. We recommend installing nox using [pipx] to have
it available globally:

```bash
python -m pip install pipx
python -m pipx install nox
nox
```

You can invoke `nox -s` to run individual sessions. For example, to install
your package into a virtual environment and run your test suite, invoke:

```bash
nox -s test
```

We also provide a nox session that creates an environment for development. The
project is installed in [editable] mode into this environment along with
linting, type checking and formatting tools. Activating it allows your editor
of choice to access these tools for, e.g., linting and autocompletion. To
create and then activate virtual environment run:

```bash
nox -s dev
source .nox/dev/bin/activate
```

Furthermore, we provide individual sessions to easily run linting, type
checking and formatting via nox. These also create editable installs. So you
can safely skip the recreation of the virtual environment and reinstallation of
your package in subsequent runs by passing the `-R` command line argument. For
example, to auto-format your code using [black], run:

```bash
nox -Rs format -- check
nox -Rs format
```

The former command allows you to inspect changes before applying them.

Note that editable installs have some caveats. In case there are issues, try
recreating environments by dropping the `-R` option. If your project is
incompatible with editable installs, adjust the `noxfile.py` to disable them.

We also provide a [pre-commit][pre] config to automate this process. It can be
set up using the following commands:

```bash
python -m pipx install pre-commit
pre-commit install
```

This blackens the source code whenever `git commit` is used.

## ToDos

### Important Features

`2023`

+ [x] New CLI structure
  + different modes:
    + MUC
    + UNSAT-CONSTRAINTS
  + can be enabled through flags
+ [x] Iterative Deltion for Multiple MUCs
  + variation of the QuickXplain algorithm : `SKIPPED`
+ [x] Finish unsat-constraints implementation for the API
  
`2024 - JAN`

+ [x] New option to enable verbose derivation output
  + `--show-decisions` with more fine grained `--decision-signature` option
+ [x] Make `--show-decisions` its own mode
+ [x] Give a warning in Transformer if control is not grounded yet
+ [ ] Documentation
  + [ ] Proper README
  + [ ] Docstrings for all API functions
  + [ ] CLI documentation with examples
  + [x] Examples folder
    + [x] Sudoku
    + [x] Graph Coloring
    + [x] N-Queens
+ [x] Error when calling `--muc` constants aren't properly kept:
  + The problem was in `AssumptionTransformer` where get_assumptions didn't have proper access to constants defined over
    the CL and the program constants
+ [x] `AssumptionTransformer` doesn't work properly on included files
  + It actually did work fine

`2024 - FEB`

+ [x] In `--show-decisions` hide INTERNAL when `--decision-signature` is active
+ [x] cleanup `DecisionOrderPropagator` print functions
+ [x] Features for `--unsat-constraints`
	+ [x] File + Line (Clickable link)
+ [x] Confusing Optimization prints during `--muc` when finding mucs in optimized Programs
+ [x] File-Link test with space in filename
  + with `urllib.parsequote`
+ [x] Write up why negated assumptions in MUC's are a problem
  + One which is currently not addressed by clingo-explaid
+ [x] Remove minimization also from `--unsat-constaints` mode
+ [x] Change file identification to use `clingo.ast.Location` instead of the subtring search and own built file tree
+ [x] Add spaces around Link to make it clickable on MAC
+ [ ] Add way for `-a` to allow for signatures without variables (`test/0`)
	
### Extra Features
+ [ ] `--unsat-constraints`:
  + [ ] Access comments in the same line as constraint
  + [ ] Currently, for multiline constraints a line number cannot be found
+ [ ] Timeout

## Problems and Limitations

### Meta-encoding based approach (ASP-Approach)

**Important Notes:**

+ The Meta-encoding approach as it stands is not fully functional

**Problem:**
  + In the meta encoding all facts (or a selection matching a certain signature) are
    transformed into assumptions which are then used as the assumption set for finding
    the MUC
  + During the MUC search when subsets of this assumption set are fixed for satisfiability
    checking it is important that even though they are not fixed, the other assumptions
    are not assumed as false but as undefined
  + This is currently not possible with the meta-encoding, since assumptions are chosen
    through a choice rule and all assumptions that aren't selected are defaulted to false
  + This doesn't allow for properly checking if such subsets entail unsatisfiability and 
    thus prevents us from finding the proper MUCs

### Specifying Assumption Set using only Signatures

**Important Notes:**

+ clingo-explaid provides the `--muc` mode which gives you Minimal Unsatisfiable Cores for a given set of assumption 
  signatures that can be defined with `-a`
+ These signatures though allow not always for finding the best fitting MUC for a given encoding, compared 
  to an assumption set generated by hand

**Problem:**

+ Imagine this [example encoding](examples/misc/bad_mucs.lp):

```MATLAB
a(1..3).
:- a(X).

unsat.
:- unsat.
```

+ So when I execute `clingexplaid examples/misc/bad_mucs.lp --muc 0` I get the MUCs:

```
MUC 1 
a(3)
MUC 2 
a(2)
MUC 3 
a(1)
MUC 4 
unsat
```

+ So you would generally expect that executing  `clingexplaid examples/misc/bad_mucs.lp --muc 0 -a/1` would return the 
  first 3 found MUCs from before
+ But what actually happens is that there are no MUCs detected:

```
NO MUCS CONTAINED: The unsatisfiability of this program is not induced by the provided assumptions
UNSATISFIABLE
```

+ This is actually due to an implicit `(unsat, False)` in the first 3 MUCs that isn't printed
+ Since the standard mode of `--muc` converts all facts to choices when no `-a` is provided `a(1)`, `a(2)`, `a(3)`, 
  and `unsat` are all converted to choices
+ We know that for the program to become satisfiable `unsat` cannot be true (line 4)
+ But since it is provided as a fact the choice rule conversion is necessary for the iterative deletion algorithm to 
  find any MUCs
+ This holds vice versa for the last MUC 4 just so that all `a/1` need to be converted to choice rules for the MUC to be
  found


[doc]: https://potassco.org/clingo/python-api/current/
[nox]: https://nox.thea.codes/en/stable/index.html
[pipx]: https://pypa.github.io/pipx/
[pre]: https://pre-commit.com/
[black]: https://black.readthedocs.io/en/stable/
[editable]: https://setuptools.pypa.io/en/latest/userguide/development_mode.html
