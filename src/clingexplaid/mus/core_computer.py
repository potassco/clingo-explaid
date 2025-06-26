"""
MUS Module: Core Computer to get Minimal Unsatisfiable Subsets
"""

import time
import warnings
from dataclasses import dataclass
from itertools import chain, combinations
from typing import Dict, Generator, Iterable, Iterator, List, Optional, Set, Tuple, Union

import clingo

from ..utils import get_solver_literal_lookup
from ..utils.types import Assumption, AssumptionSet


@dataclass
class UnsatisfiableSubset:
    """Container class for unsatisfiable subsets"""

    assumptions: Set[Assumption]
    minimal: bool = False

    @staticmethod
    def _render_assumption(assumption: Assumption) -> str:  # nocoverage
        if isinstance(assumption, int):
            return str(int)
        symbol, positive = assumption
        out = str(symbol)
        out += "[+]" if positive else "[-]"
        return out

    def __iter__(self) -> Iterator[Union[tuple[clingo.Symbol, bool], int]]:
        return self.assumptions.__iter__()

    def __str__(self) -> str:  # nocoverage
        out = "UnsatisfiableSubset("
        out += "assumptions={"
        out += ",".join([UnsatisfiableSubset._render_assumption(a) for a in self.assumptions])
        out += "}, minimal="
        out += str(self.minimal)
        out += ")"
        return out

    __repr__ = __str__


class CoreComputer:
    """
    A container class that allows for a passed program_string and assumption_set to compute a minimal unsatisfiable
    core.
    """

    def __init__(self, control: clingo.Control, assumption_set: AssumptionSet):
        self.control = control
        self.assumption_set = assumption_set
        self.literal_lookup = get_solver_literal_lookup(control=self.control)
        self.minimal: Optional[UnsatisfiableSubset] = None
        self._assumptions_minimal: Set[Assumption] = set()
        self._assumptions_removed: Set[Assumption] = set()

    def _is_satisfiable(self, assumptions: Optional[AssumptionSet] = None) -> bool:
        """
        Internal function that is used to make the single solver calls for finding the minimal unsatisfiable subset.
        """
        if assumptions is None:
            assumptions = self.assumption_set

        with self.control.solve(assumptions=list(assumptions), yield_=True) as solve_handle:
            satisfiable = bool(solve_handle.get().satisfiable)

        return satisfiable

    def _compute_single_minimal(
        self, assumptions: Optional[AssumptionSet] = None, timeout: Optional[float] = None
    ) -> UnsatisfiableSubset:
        """
        Function to compute a single minimal unsatisfiable subset from the passed set of assumptions and the program of
        the CoreComputer. If there is no minimal unsatisfiable subset, since for example the program with assumptions
        assumed is satisfiable, an empty set is returned. The algorithm that is used to compute this minimal
        unsatisfiable core is the iterative deletion algorithm.
        """
        time_start = time.perf_counter()

        if assumptions is None:
            assumptions = self.assumption_set

        # Reset progress set
        self._assumptions_minimal = set()

        # check that the assumption set isn't empty
        if not assumptions:
            warnings.warn("A minimal unsatisfiable subset cannot be computed on an empty assumption set")

        # check if the problem with the full assumption set is unsatisfiable in the first place, and if not skip the
        # rest of the algorithm and return an empty set.
        satisfiable = self._is_satisfiable(assumptions=assumptions)
        if satisfiable:
            return UnsatisfiableSubset(set())

        working_set = set(assumptions)
        timeout_reached = False

        for assumption in assumptions:
            # remove the current assumption from the working set
            working_set.remove(assumption)

            satisfiable = self._is_satisfiable(assumptions=working_set.union(self._assumptions_minimal))
            # if the working set now becomes satisfiable without the assumption it is added to the mus_members
            if satisfiable:
                self._assumptions_minimal.add(assumption)
                # every time we discover a new mus member we also check if all currently found mus members already
                # suffice to make the instance unsatisfiable. If so we can stop the search sice we found our mus.
                if not self._is_satisfiable(assumptions=self._assumptions_minimal):
                    break
            else:
                # Remove the current assumption since it's not part of the mus
                self._assumptions_removed.add(assumption)

            # Check after each assumption if timeout is reached
            if timeout is not None and time_start + timeout < time.perf_counter():
                timeout_reached = True
                break

        return UnsatisfiableSubset(self._assumptions_minimal, minimal=not timeout_reached)

    def shrink(
        self, assumptions: Optional[AssumptionSet] = None, timeout: Optional[float] = None
    ) -> UnsatisfiableSubset:
        """
        This function applies the unsatisfiable subset minimization (`self._compute_single_minimal`) on the assumptions
        set `assumptions` and stores the resulting MUS inside `self.minimal`.

        Returns the MUS as a set of assumptions.
        """
        self.minimal = self._compute_single_minimal(assumptions=assumptions, timeout=timeout)
        return self.minimal

    def get_multiple_minimal(
        self, max_mus: Optional[int] = None, timeout: Optional[float] = None
    ) -> Generator[UnsatisfiableSubset, None, None]:
        """
        This function generates all minimal unsatisfiable subsets of the provided assumption set. It implements the
        generator pattern since finding all mus of an assumption set is exponential in nature and the search might not
        fully complete in reasonable time. The parameter `max_mus` can be used to specify the maximum number of
        mus that are found before stopping the search.
        """
        deadline = time.perf_counter() + timeout if timeout is not None else None

        assumptions = self.assumption_set
        assumption_powerset = chain.from_iterable(
            combinations(assumptions, r) for r in reversed(range(len(list(assumptions)) + 1))
        )

        found_sat: List[AssumptionSet] = []
        found_mus: List[AssumptionSet] = []

        for current_subset in (set(s) for s in assumption_powerset):
            time_remaining = deadline - time.perf_counter() if deadline is not None else None
            # stop if timeout is specified and deadline is reached
            if time_remaining is not None and time_remaining <= 0:
                warnings.warn("Timeout was reached")
                break
            # skip if empty subset
            if len(current_subset) == 0:
                continue
            # skip if an already found satisfiable subset is superset
            if any(set(sat).issuperset(current_subset) for sat in found_sat):
                continue
            # skip if an already found mus is a subset
            if any(set(mus).issubset(current_subset) for mus in found_mus):
                continue

            mus = self._compute_single_minimal(assumptions=current_subset, timeout=time_remaining)

            # if the current subset wasn't unsatisfiable store this info and continue
            if len(list(mus)) == 0:
                found_sat.append(current_subset)
                continue

            # if iterative deletion finds a mus that wasn't discovered before update sets and yield
            if mus not in found_mus:
                found_mus.append(mus)
                yield mus
                # if the maximum mus amount is found stop search
                if max_mus is not None and len(found_mus) == max_mus:
                    break

    def mus_to_string(
        self,
        mus: Iterable[Union[Tuple[clingo.Symbol, bool], int]],
        literal_lookup: Optional[Dict[int, clingo.Symbol]] = None,
    ) -> Set[str]:
        """
        Converts a MUS into a set containing the string representations of the contained assumptions
        """
        # take class literal_lookup as default if no other is provided
        if literal_lookup is None:
            literal_lookup = self.literal_lookup

        mus_string = set()
        for a in mus:
            if isinstance(a, int):
                mus_string.add(str(literal_lookup[a]))
            else:
                mus_string.add(str(a[0]))
        return mus_string
