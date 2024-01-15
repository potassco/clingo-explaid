"""
Unsatisfiable Core Utilities
"""
import time
from typing import Optional, Set, Tuple
from itertools import chain, combinations

import clingo

from . import Assumption, AssumptionSet, SymbolSet, get_solver_literal_lookup


class CoreComputer:
    """
    A container class that allows for a passed program_string and assumption_set to compute a minimal unsatisfiable
    core.
    """

    def __init__(self, control: clingo.Control, assumption_set: AssumptionSet):
        self.control = control
        self.assumption_set = assumption_set
        self.literal_lookup = get_solver_literal_lookup(control=self.control)
        self.minimal: Optional[AssumptionSet] = None

    def _solve(
        self, assumptions: Optional[AssumptionSet] = None
    ) -> Tuple[bool, SymbolSet, SymbolSet]:
        """
        Internal function that is used to make the single solver calls for finding the minimal unsatisfiable core.
        """
        if assumptions is None:
            assumptions = self.assumption_set

        with self.control.solve(assumptions=list(assumptions), yield_=True) as solve_handle:  # type: ignore[union-attr]
            satisfiable = bool(solve_handle.get().satisfiable)
            model = (
                solve_handle.model().symbols(atoms=True)
                if solve_handle.model() is not None
                else []
            )
            core = {
                self.literal_lookup[literal_id] for literal_id in solve_handle.core()
            }

        return satisfiable, set(model), core

    def _compute_single_minimal(
        self, assumptions: Optional[AssumptionSet] = None
    ) -> AssumptionSet:
        """
        Function to compute a single minimal unsatisfiable core from the passed set of assumptions and the program of
        the CoreComputer. If there is not minimal unsatisfiable core, since for example the program with assumptions
        assumed is satisfiable, an empty set is returned. The algorithm that is used to compute this minimal
        unsatisfiable core is the iterative deletion algorithm.
        """
        if assumptions is None:
            assumptions = self.assumption_set

        # check that the assumption set isn't empty
        if not assumptions:
            raise ValueError(
                "A minimal unsatisfiable core cannot be computed on an empty assumption set"
            )

        # check if the problem with the full assumption set is unsatisfiable in the first place, and if not skip the
        # rest of the algorithm and return an empty set.
        satisfiable, _, _ = self._solve(assumptions=assumptions)
        if satisfiable:
            return set()

        muc_members: Set[Assumption] = set()
        working_set = set(assumptions)

        for assumption in assumptions:
            # remove the current assumption from the working set
            working_set.remove(assumption)

            satisfiable, _, _ = self._solve(assumptions=working_set.union(muc_members))
            # if the working set now becomes satisfiable without the assumption it is added to the muc_members
            if satisfiable:
                muc_members.add(assumption)
                # every time we discover a new muc member we also check if all currently found muc members already
                # suffice to make the instance unsatisfiable. If so we can stop the search sice we fund our muc.
                if not self._solve(assumptions=muc_members)[0]:
                    break

        return muc_members

    def shrink(self, assumptions: Optional[AssumptionSet] = None) -> None:
        """
        This function applies the unsatisfiable core minimization (`self._compute_single_minimal`) on the assumptions
        set `assumptions` and stores the resulting MUC inside `self.minimal`.
        """
        self.minimal = self._compute_single_minimal(assumptions=assumptions)

    def get_multiple_minimal(self, max_mucs: Optional[int] = None):
        """
        This function generates all minimal unsatisfiable cores of the provided assumption set. It implements the
        generator pattern since finding all mucs of an assumption set is exponential in nature and the search might not
        fully complete in reasonable time. The parameter `max_mucs` can be used to specify the maximum number of
        mucs that are found before stopping the search.
        """
        assumptions = self.assumption_set
        assumption_powerset = chain.from_iterable(
            combinations(assumptions, r)
            for r in reversed(range(len(list(assumptions)) + 1))
        )

        found_sat = []
        found_mucs = []

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

            muc = self._compute_single_minimal(assumptions=current_subset)

            # if the current subset wasn't unsatisfiable store this info and continue
            if len(list(muc)) == 0:
                found_sat.append(current_subset)
                continue

            # if iterative deletion finds a muc that wasn't discovered before update sets and yield
            if muc not in found_mucs:
                found_mucs.append(muc)
                yield muc
                # if the maximum muc amount is found stop search
                if max_mucs is not None and len(found_mucs) == max_mucs:
                    break


__all__ = [
    CoreComputer.__name__,
]
