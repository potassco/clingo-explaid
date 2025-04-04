import os

import nox

nox.options.sessions = "lint_pylint", "typecheck", "test"

EDITABLE_TESTS = True
PYTHON_VERSIONS = None
if "GITHUB_ACTIONS" in os.environ:
    PYTHON_VERSIONS = ["3.13", "3.12", "3.11"]
    EDITABLE_TESTS = False


@nox.session
def doc(session):
    """
    Build the documentation.

    Accepts the following arguments:
    - open: open documentation after build
    - clean: clean up the build folder
    - <target> <options>: build the given <target> with the given <options>
    """
    target = "html"
    options = []
    open_doc = "open" in session.posargs
    clean = "clean" in session.posargs

    if open_doc:
        session.posargs.remove("open")
    if clean:
        session.posargs.remove("clean")

    if session.posargs:
        target = session.posargs[0]
        options = session.posargs[1:]

    session.install("-e", ".[doc]")
    session.cd("doc")
    if clean:
        session.run("rm", "-rf", "_build")
    session.run("sphinx-build", "-M", target, ".", "_build", *options)
    if open_doc:
        session.run("open", "_build/html/index.html")


@nox.session
def dev(session):
    """
    Create a development environment in editable mode.

    Activate it by running `source .nox/dev/bin/activate`.
    """
    session.install("-e", ".[dev]")


@nox.session
def lint_pylint(session):
    """
    Run pylint.
    """
    session.install("-e", ".[lint_pylint]")
    session.run("pylint", "clingexplaid", "tests")


@nox.session
def typecheck(session):
    """
    Typecheck the code using mypy.
    """
    session.install("-e", ".[typecheck]")
    session.run("mypy", "--strict", "-p", "clingexplaid", "-p", "tests")


@nox.session(python=PYTHON_VERSIONS)
def test(session):
    """
    Run the tests.

    Accepts an additional arguments which are passed to the unittest module.
    This can for example be used to selectively run test cases.
    """

    args = [".[test]"]
    if EDITABLE_TESTS:
        args.insert(0, "-e")
    session.install(*args)
    if session.posargs:
        session.run("coverage", "run", "-m", "unittest", session.posargs[0], "-v")
    else:
        session.run("coverage", "run", "-m", "unittest", "discover", "-v")
        session.run("coverage", "report", "-m", "--fail-under=100")
