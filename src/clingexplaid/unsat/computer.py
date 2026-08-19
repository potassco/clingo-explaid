"""
Container class for subset computation
"""

from typing import Generator, Iterable, Type

import clingo
from clingo import Symbol
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
    Provides methods for computing fundamental subsets of unsatisfiable problems
    """

    def __init__(
        self,
        control: clingo.Control,
        assumptions: Iterable[int | tuple[Symbol, bool]],
        explorer: Type[Explorer] = ExplorerPowerset,
    ):
        self.control = control
        self.literal_lookup: dict[int, Symbol] = {}
        self.symbol_lookup: dict[Symbol, int] = {}

        self._build_lookups()

        self.assumption_literals: set[int] = self._to_assumption_literals(assumptions)
        self.explorer = explorer(assumptions=self._wrap_assumption_literals(self.assumption_literals))

    def _wrap_assumption_literals(self, literals: Iterable[int]) -> set[AssumptionWrapper]:
        return {self._get_assumption_wrapper(literal) for literal in literals}

    def _get_assumption_wrapper(self, literal: int) -> AssumptionWrapper:
        return AssumptionWrapper(literal=literal, symbol=self.literal_lookup[abs(literal)], sign=literal >= 0)

    def _build_lookups(self) -> None:
        """Build up the literal and symbol lookup dictionaries from a grounded clingo Control object"""
        self.literal_lookup = {}
        self.symbol_lookup = {}
        for atom in self.control.symbolic_atoms:
            self.literal_lookup[abs(atom.literal)] = atom.symbol
            self.symbol_lookup[atom.symbol] = abs(atom.literal)

    def _build_subset(self, assumptions: set[int], type: type[Subset]) -> Subset:
        """Build up an unsatisfiable subset from the given set of assumptions"""
        wrapper_set = set()
        for a_literal in assumptions:
            assumption_symbol = self.literal_lookup[abs(a_literal)]
            a_sign = a_literal >= 0
            a_wrapper = AssumptionWrapper(literal=a_literal, symbol=assumption_symbol, sign=a_sign)
            wrapper_set.add(a_wrapper)
        return type(assumptions=wrapper_set)

    def _to_assumption_literals(self, assumptions: Iterable[int | tuple[Symbol, bool]]) -> set[int]:
        """Convert assumptions to literal representation, e.g.: (Symbol, bool) -> int"""
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

    def mus(
        self,
        assumptions: Iterable[int | tuple[Symbol, bool]] | None = None,
        timeout: float | None = None,
    ) -> Subset:
        """
        Find a singlular MUS via linear elimination
        """
        literals: set[int] = self._to_assumption_literals(
            assumptions if assumptions is not None else self.assumption_literals
        )

        mus, interrupted = LinearElimination(self.control).shrink_known(literals, timeout)

        if interrupted:
            return self._build_subset(mus, UnsatisfiableSubset)
        else:
            return self._build_subset(mus, MinimalUnsatisfiableSubset)

    def multiple(
        self,
        types: set[type[MinimalUnsatisfiableSubset] | type[MaximalSatisfiableSubset] | type[MinimalCorrectionSet]] = {
            MinimalUnsatisfiableSubset
        },
        maximum: int | None = None,
        timeout: float | None = None,
    ) -> Generator[Subset, None, None]:
        """
        Find multiple fundamental subsets filtered by the `types` argument.
        """
        literals: set[int] = self._to_assumption_literals(self.assumption_literals)

        lattice = AssumptionsLattice(literals, bias=True)
        strategy = LinearElimination(self.control)

        algorithm = MARCO(lattice, strategy)

        found = 0
        for subset_type, subset in algorithm:
            if subset_type == "mus" and MinimalUnsatisfiableSubset in types:
                found += 1
                yield self._build_subset(subset, MinimalUnsatisfiableSubset)
            elif subset_type == "mss" and MaximalSatisfiableSubset in types:
                found += 1
                yield self._build_subset(subset, MaximalSatisfiableSubset)
                mcs = literals.intersection(subset)
                yield self._build_subset(mcs, MinimalCorrectionSet)

            # exit on maximum subset reached
            if maximum is not None and found >= maximum:
                return
