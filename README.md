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

## Experimental Features

### Meta-encoding based approach (ASP-Approach)

Using the `--muc-method` or `-m` option the approach for finding the MUCs can 
be switched from the iterative deletion algorithm to the meta encoding based 
approach.

+ `-m 1` [default] Iterative deletion approach
+ `-m 2` Meta-encoding approach

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

[doc]: https://potassco.org/clingo/python-api/current/
[nox]: https://nox.thea.codes/en/stable/index.html
[pipx]: https://pypa.github.io/pipx/
[pre]: https://pre-commit.com/
[black]: https://black.readthedocs.io/en/stable/
[editable]: https://setuptools.pypa.io/en/latest/userguide/development_mode.html
