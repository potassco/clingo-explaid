"""Container class for subset computation."""

import time
import warnings
from typing import Generator, Iterable, Type, cast

import clingo
from clingo import SolveHandle, Symbol
from musclingo.algorithms.marco import MARCO
from musclingo.lattice import AssumptionsLattice
from musclingo.shrink import LinearElimination

from .explorers import Explorer, ExplorerPowerset
from .sets import (
    MaximalSatisfiableSubset,
    MinimalCorrectionSet,
    MinimalUnsatisfiableSubset,
    Subset,
    UnsatisfiableSubset,
)
from .utils import AssumptionWrapper


class SubsetComputer:
    """
    Compute fundamental subsets of unsatisfiable problems.
    """

    def __init__(
        self,
        control: clingo.Control,
        assumptions: Iterable[int | tuple[Symbol, bool]],
        explorer: Type[Explorer] = ExplorerPowerset,
    ) -> None:
        self.control = control
        self.literal_lookup: dict[int, Symbol] = {}
        self.symbol_lookup: dict[Symbol, int] = {}

        self._build_lookups()

        self.assumption_literals: set[int] = self._to_assumption_literals(assumptions)
        self.explorer = explorer(assumptions={self._wrap(literal) for literal in self.assumption_literals})
        self._last_mus: MinimalUnsatisfiableSubset | None = None
        self._last_mss: MaximalSatisfiableSubset | None = None
        self._last_mcs: MinimalCorrectionSet | None = None

    def _wrap(self, literal: int) -> AssumptionWrapper:
        return AssumptionWrapper(literal=literal, symbol=self.literal_lookup[abs(literal)], sign=literal >= 0)

    def _build_lookups(self) -> None:
        self.literal_lookup = {}
        self.symbol_lookup = {}
        for atom in self.control.symbolic_atoms:
            self.literal_lookup[abs(atom.literal)] = atom.symbol
            self.symbol_lookup[atom.symbol] = abs(atom.literal)

    def _build_subset(self, assumptions: set[int], type: type[Subset]) -> Subset:
        wrapper_set = set()
        for a_literal in assumptions:
            assumption_symbol = self.literal_lookup[abs(a_literal)]
            a_sign = a_literal >= 0
            a_wrapper = AssumptionWrapper(literal=a_literal, symbol=assumption_symbol, sign=a_sign)
            wrapper_set.add(a_wrapper)
        return type(assumptions=wrapper_set)

    def _to_assumption_literals(self, assumptions: Iterable[int | tuple[Symbol, bool]]) -> set[int]:
        converted = set()
        for assumption in assumptions:
            if isinstance(assumption, int):
                converted.add(assumption)
            elif isinstance(assumption[0], Symbol):
                (assumption_symbol, assumption_sign) = assumption
                a_literal = self.symbol_lookup[assumption_symbol]
                a_sign_factor = 1 if assumption_sign else -1
                converted.add(a_literal * a_sign_factor)
        return converted

    def is_valid(self, assumptions: set[int]) -> bool:
        """
        Check whether the program with the provided assumptions is valid.

        Parameters
        ----------
        assumptions
            A set of assumption literals to check the `SubsetComputer`'s program's validity against.

        Returns
        -------
        valid
            Indicates wheter the `SubsetComputer`'s input is valid.
        """
        try:
            with self.control.solve(assumptions=list(assumptions), yield_=True) as solve_handle:
                assert not cast(SolveHandle, solve_handle).get().satisfiable
            return True
        except AssertionError:
            return False

    def mus(
        self,
        assumptions: Iterable[int | tuple[Symbol, bool]] | None = None,
        timeout: float | None = None,
    ) -> Subset:
        """
        Find a singlular MUS via linear elimination.

        Parameters
        ----------
        assumptions
            A set of assumption literals that form an unsatisfiable subset (US).
        timeout
            Sets a timeout in seconds, that if exceeded stops the search and returns the already found MUS literals.

        Returns
        -------
        mus
            A `MinimalUnsatisfiableSubset` if one is found or an `UnsatisfiableSubset` if `timeout` is exceeded or the
            input is invalid.
        """
        literals: set[int] = self._to_assumption_literals(
            assumptions if assumptions is not None else self.assumption_literals
        )

        if not self.is_valid(literals):
            return UnsatisfiableSubset(set())

        mus, interrupted = LinearElimination(self.control).shrink_known(literals, timeout)

        if interrupted:
            return self._build_subset(mus, UnsatisfiableSubset)
        else:
            mus_out = cast(MinimalUnsatisfiableSubset, self._build_subset(mus, MinimalUnsatisfiableSubset))
            self._last_mus = mus_out
            return mus_out

    def mss(
        self,
        assumptions: Iterable[int | tuple[Symbol, bool]] | None = None,
    ) -> MaximalSatisfiableSubset | None:
        """
        Find a singlular MSS. This method is a wrapper around `SubsetComputer.multiple()`.

        Parameters
        ----------
        assumptions
            A set of assumption literals that form an unsatisfiable subset (US).

        Returns
        -------
        mss
            A `MaximalSatisfiableSubset` if one is found or `None` if the input is invalid.
        """
        for mss in self.multiple(types={MaximalSatisfiableSubset}, assumptions=assumptions, maximum=1):
            return cast(MaximalSatisfiableSubset, mss)

    def mcs(
        self,
        assumptions: Iterable[int | tuple[Symbol, bool]] | None = None,
    ) -> MinimalCorrectionSet | None:
        """
        Find a singlular MCS. This method is a wrapper around `SubsetComputer.multiple()`.

        Parameters
        ----------
        assumptions
            A set of assumption literals that form an unsatisfiable subset (US).

        Returns
        -------
        mcs
            A `MinimalCorrectionSet` if one is found or `None` if the input is invalid.
        """
        for mcs in self.multiple(types={MinimalCorrectionSet}, assumptions=assumptions, maximum=1):
            return cast(MinimalCorrectionSet, mcs)

    def multiple(
        self,
        assumptions: Iterable[int | tuple[Symbol, bool]] | None = None,
        types: set[type[MinimalUnsatisfiableSubset] | type[MaximalSatisfiableSubset] | type[MinimalCorrectionSet]]
        | None = None,
        maximum: int | None = None,
        timeout: float | None = None,
    ) -> Generator[Subset, None, None]:
        """
        Find multiple fundamental subsets filtered by the `types` argument.

        Parameters
        ----------
        assumptions
            A set of assumption literals that form an unsatisfiable subset (US).
        types
            A set of `Subset` classes that filters which kinds of subsets are yielded in the search.
            Equals `{MinimalUnsatisfiableSubset}` by default.
        maximum
            The maximum amout of subsets to be found. The search is stopped after this amout is reached.
        timeout
            Sets a timeout in seconds, that if exceeded stops the subset search.

        Yields
        ------
        subset
            A subets matching the types specified in `types`.
        """
        types = types if types is not None else {MinimalUnsatisfiableSubset}
        assumptions = assumptions if assumptions is not None else self.assumption_literals
        literals: set[int] = self._to_assumption_literals(assumptions)

        if not self.is_valid(literals):
            return

        lattice = AssumptionsLattice(literals, bias=True)
        strategy = LinearElimination(self.control)

        algorithm = MARCO(lattice, strategy)

        t_start = time.perf_counter()
        found = 0
        for subset_type, subset in algorithm:
            if subset_type == "mus" and MinimalUnsatisfiableSubset in types:
                found += 1
                mus_out = cast(MinimalUnsatisfiableSubset, self._build_subset(subset, MinimalUnsatisfiableSubset))
                self._last_mus = mus_out
                yield mus_out
            elif subset_type == "mss" and MaximalSatisfiableSubset in types:
                found += 1
                mss_out = cast(MaximalSatisfiableSubset, self._build_subset(subset, MaximalSatisfiableSubset))
                self._last_mss = mss_out
                yield mss_out
                mcs = literals.intersection(subset)
                mcs_out = cast(MinimalCorrectionSet, self._build_subset(mcs, MinimalCorrectionSet))
                self._last_mcs = mcs_out
                yield mcs_out

            # exit on maximum subset reached
            if maximum is not None and found >= maximum:
                return
            # exit on timeout reached
            if timeout is not None and time.perf_counter() >= t_start + timeout:
                warnings.warn("Timeout was reached when exploring subset space of unsatisfiable program", stacklevel=2)
                return

    @property
    def last_mus(self) -> MinimalUnsatisfiableSubset | None:
        """The last MUS that was found."""
        return self._last_mus
