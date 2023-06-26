from typing import Set, Tuple, Optional

import clingo

from . import get_solver_literal_lookup, LiteralSet, SymbolSet


class CoreComputer:
    """
    A container class that allows for a passed program_string and assumption_set to compute a minimal unsatisfiable
    core.
    """

    def __init__(self, program_string: str, assumption_set: LiteralSet, control: Optional[clingo.Control] = None):
        if control is None:
            control = clingo.Control()
        self.control = control
        self.assumption_set = assumption_set
        self.program_string = program_string

        self.control.add("base", [], program_string)
        self.control.ground([("base", [])])

        self.literal_lookup = get_solver_literal_lookup(control=self.control)

    def _solve(self, assumptions: Optional[LiteralSet] = None) -> Tuple[bool, SymbolSet, LiteralSet]:
        """
        Internal function that is used to make the single solver calls for finding the minimal unsatisfiable core.
        """
        if assumptions is None:
            assumptions = self.assumption_set

        with self.control.solve(assumptions=list(assumptions), yield_=True) as solve_handle:
            satisfiable = solve_handle.get().satisfiable
            model = solve_handle.model().symbols(atoms=True) if solve_handle.model() is not None else []
            core = {self.literal_lookup[literal_id] for literal_id in solve_handle.core()}

        return satisfiable, set(model), core

    def _compute_single_minimal(self, assumptions: Optional[LiteralSet] = None) -> LiteralSet:
        """
        Function to compute a single minimal unsatisfiable core from the passed set of assumptions and the program of
        the CoreComputer. If there is not minimal unsatisfiable core, since for example the program with assumptions
        assumed is satisfiable, an empty set is returned. The algorithm that is used to compute this minimal
        unsatisfiable core is the iterative deletion algorithm.
        """
        if assumptions is None:
            assumptions = self.assumption_set

        # check if the problem with the full assumption set is unsatisfiable in the first place, and if not skip the
        # rest of the algorithm and return an empty set.
        satisfiable, _, _ = self._solve(assumptions=assumptions)
        if satisfiable:
            return set()

        muc_members = set()
        working_set = set(assumptions)
        for assumption in self.assumption_set:
            # remove the current assumption from the working set
            working_set.remove(assumption)

            satisfiable, _, _ = self._solve(assumptions=working_set)
            # if the working set now becomes satisfiable without the assumption it is added to the muc_members
            if satisfiable:
                muc_members.add(assumption)
                # every time we discover a new muc member we also check if all currently found muc members already
                # suffice to make the instance unsatisfiable. If so we can stop the search sice we fund our muc.
                if not self._solve(assumptions=muc_members)[0]:
                    break

        return muc_members

    def get_minimal(self):
        return self._compute_single_minimal()

    def __str__(self):
        return f"<CoreComputer: {len(self.assumption_set)} assumptions>"

    __repr__ = __str__


__all__ = [
    CoreComputer.__name__,
]
