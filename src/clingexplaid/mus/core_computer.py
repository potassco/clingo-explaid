"""
MUS Module: Core Computer to get Minimal Unsatisfiable Subsets
"""

import asyncio
import warnings
from dataclasses import dataclass
from itertools import chain, combinations
from typing import Dict, Generator, Iterable, Iterator, List, Optional, Set, Tuple, Union

import clingo

from ..utils import get_solver_literal_lookup
from ..utils.types import Assumption, AssumptionSet, SymbolSet


@dataclass
class UnsatisfiableSubset:
    """Container class for unsatisfiable subsets"""

    assumptions: Set[Assumption]
    minimal: bool = False

    def __iter__(self) -> Iterator[Union[tuple[clingo.Symbol, bool], int]]:
        return self.assumptions.__iter__()


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

    def _solve(self, assumptions: Optional[AssumptionSet] = None) -> Tuple[bool, SymbolSet, SymbolSet]:
        """
        Internal function that is used to make the single solver calls for finding the minimal unsatisfiable subset.
        """
        if assumptions is None:
            assumptions = self.assumption_set

        with self.control.solve(assumptions=list(assumptions), yield_=True) as solve_handle:
            satisfiable = bool(solve_handle.get().satisfiable)
            model = solve_handle.model().symbols(atoms=True) if solve_handle.model() is not None else []
            core = {self.literal_lookup[literal_id] for literal_id in solve_handle.core()}

        return satisfiable, set(model), core

    async def _compute_single_minimal(self, assumptions: Optional[AssumptionSet] = None) -> UnsatisfiableSubset:
        """
        Function to compute a single minimal unsatisfiable subset from the passed set of assumptions and the program of
        the CoreComputer. If there is no minimal unsatisfiable subset, since for example the program with assumptions
        assumed is satisfiable, an empty set is returned. The algorithm that is used to compute this minimal
        unsatisfiable core is the iterative deletion algorithm.
        """
        if assumptions is None:
            assumptions = self.assumption_set

        # Reset progress set
        self._assumptions_minimal = set()

        # check that the assumption set isn't empty
        if not assumptions:
            warnings.warn("A minimal unsatisfiable subset cannot be computed on an empty assumption set")

        # check if the problem with the full assumption set is unsatisfiable in the first place, and if not skip the
        # rest of the algorithm and return an empty set.
        satisfiable, _, _ = self._solve(assumptions=assumptions)
        if satisfiable:
            return UnsatisfiableSubset(set())

        working_set = set(assumptions)

        for assumption in assumptions:
            # remove the current assumption from the working set
            working_set.remove(assumption)

            satisfiable, _, _ = self._solve(assumptions=working_set.union(self._assumptions_minimal))
            # if the working set now becomes satisfiable without the assumption it is added to the mus_members
            if satisfiable:
                self._assumptions_minimal.add(assumption)
                # every time we discover a new mus member we also check if all currently found mus members already
                # suffice to make the instance unsatisfiable. If so we can stop the search sice we found our mus.
                if not self._solve(assumptions=self._assumptions_minimal)[0]:
                    break
            else:
                # Remove the current assumption since it's not part of the mus
                self._assumptions_removed.add(assumption)

            # Do a very short wait every time to allow for async timeout interruption
            await asyncio.sleep(0.0000001)

        return UnsatisfiableSubset(self._assumptions_minimal, minimal=True)

    async def _shrink_unsatisfiable_subset(
        self, assumptions: Optional[AssumptionSet] = None, timeout: Optional[float] = None
    ) -> UnsatisfiableSubset:
        timeout_occurred = False
        try:
            await asyncio.wait_for(self._compute_single_minimal(assumptions=assumptions), timeout=timeout)
            unsat_subset = self._assumptions_minimal
        except TimeoutError:
            timeout_occurred = True
            warnings.warn(
                "Timeout encountered while computing unsatisfiable subset, "
                "intermediate unsatisfiable subset is returned"
            )
            # Remove the already excluded assumptions from the original set and return them
            provided_assumptions = set(assumptions) if assumptions is not None else set(self.assumption_set)
            unsat_subset = provided_assumptions.difference(self._assumptions_removed)
        return UnsatisfiableSubset(unsat_subset, minimal=not timeout_occurred)

    def shrink(
        self, assumptions: Optional[AssumptionSet] = None, timeout: Optional[float] = None
    ) -> UnsatisfiableSubset:
        """
        This function applies the unsatisfiable subset minimization (`self._compute_single_minimal`) on the assumptions
        set `assumptions` and stores the resulting MUS inside `self.minimal`.

        Returns the MUS as a set of assumptions.
        """
        self.minimal = asyncio.run(self._shrink_unsatisfiable_subset(assumptions=assumptions, timeout=timeout))
        return self.minimal

    def get_multiple_minimal(self, max_mus: Optional[int] = None) -> Generator[UnsatisfiableSubset, None, None]:
        """
        This function generates all minimal unsatisfiable subsets of the provided assumption set. It implements the
        generator pattern since finding all mus of an assumption set is exponential in nature and the search might not
        fully complete in reasonable time. The parameter `max_mus` can be used to specify the maximum number of
        mus that are found before stopping the search.
        """
        assumptions = self.assumption_set
        assumption_powerset = chain.from_iterable(
            combinations(assumptions, r) for r in reversed(range(len(list(assumptions)) + 1))
        )

        found_sat: List[AssumptionSet] = []
        found_mucs: List[AssumptionSet] = []

        for current_subset in (set(s) for s in assumption_powerset):
            # skip if empty subset
            if len(current_subset) == 0:
                continue
            # skip if an already found satisfiable subset is superset
            if any(set(sat).issuperset(current_subset) for sat in found_sat):
                continue
            # skip if an already found muc is a subset
            if any(set(muc).issubset(current_subset) for muc in found_mucs):
                continue

            muc = asyncio.run(self._compute_single_minimal(assumptions=current_subset))

            # if the current subset wasn't unsatisfiable store this info and continue
            if len(list(muc)) == 0:
                found_sat.append(current_subset)
                continue

            # if iterative deletion finds a muc that wasn't discovered before update sets and yield
            if muc not in found_mucs:
                found_mucs.append(muc)
                yield muc
                # if the maximum muc amount is found stop search
                if max_mus is not None and len(found_mucs) == max_mus:
                    break

    def mus_to_string(
        self,
        muc: Iterable[Union[Tuple[clingo.Symbol, bool], int]],
        literal_lookup: Optional[Dict[int, clingo.Symbol]] = None,
    ) -> Set[str]:
        """
        Converts a MUS into a set containing the string representations of the contained assumptions
        """
        # take class literal_lookup as default if no other is provided
        if literal_lookup is None:
            literal_lookup = self.literal_lookup

        mus_string = set()
        for a in muc:
            if isinstance(a, int):
                mus_string.add(str(literal_lookup[a]))
            else:
                mus_string.add(str(a[0]))
        return mus_string
