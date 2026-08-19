"""
MUS Module: Core Computer to get Minimal Unsatisfiable Subsets
"""

from typing import Generator, Iterable, Type

import clingo
from clingo import Symbol
from musclingo.algorithms.marco import MARCO
from musclingo.lattice import AssumptionsLattice
from musclingo.shrink import LinearElimination

from .explorers import Explorer, ExplorerPowerset
from .sets import Subset, SubsetType
from .utils import AssumptionWrapper


class CoreComputer:
    """
    A container class that allows for a passed program_string and assumption_set to compute a minimal unsatisfiable
    core.
    """

    def __init__(
        self,
        control: clingo.Control,
        assumption_set: Iterable[int | tuple[Symbol, bool]],
        explorer: Type[Explorer] = ExplorerPowerset,
    ):
        self.control = control
        self.literal_lookup: dict[int, Symbol] = {}
        self.symbol_lookup: dict[Symbol, int] = {}
        self.minimal: Subset | None = None
        self._assumptions_minimal: set[int] = set()

        self._build_lookups()

        self.assumptions: set[int] = self._to_assumption_literals(assumption_set)
        self.explorer = explorer(assumptions=self._wrap_assumption_literals(self.assumptions))

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

    def _build_unsatisfiable_subset(self, assumptions: set[int], minimal: bool) -> Subset:
        """Build up an unsatisfiable subset from the given set of assumptions"""
        wrapper_set = set()
        for a_literal in assumptions:
            assumption_symbol = self.literal_lookup[abs(a_literal)]
            a_sign = a_literal >= 0
            a_wrapper = AssumptionWrapper(literal=a_literal, symbol=assumption_symbol, sign=a_sign)
            wrapper_set.add(a_wrapper)
        return Subset(type=SubsetType.MinimalUnsatisfiableSubset, assumptions=wrapper_set)

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

    def _compute_single_minimal(
        self,
        assumptions: Iterable[int | tuple[Symbol, bool]] | None = None,
        timeout: float | None = None,
    ) -> Subset:
        """
        Function to compute a single minimal unsatisfiable subset from the passed set of assumptions and the program of
        the CoreComputer. If there is no minimal unsatisfiable subset, since for example the program with assumptions
        assumed is satisfiable, an empty set is returned. The algorithm that is used to compute this minimal
        unsatisfiable core is the iterative deletion algorithm.
        """
        _assumptions: set[int] = self._to_assumption_literals(
            assumptions if assumptions is not None else self.assumptions
        )

        mus = LinearElimination(self.control).shrink_known(_assumptions)

        return self._build_unsatisfiable_subset(mus, minimal=True)

    def get_multiple_minimal(
        self, max_mus: int | None = None, timeout: float | None = None
    ) -> Generator[Subset, None, None]:
        """
        This function generates all minimal unsatisfiable subsets of the provided assumption set. It implements the
        generator pattern since finding all mus of an assumption set is exponential in nature and the search might not
        fully complete in reasonable time. The parameter `max_mus` can be used to specify the maximum number of
        mus that are found before stopping the search.
        """
        _assumptions: set[int] = self._to_assumption_literals(self.assumptions)

        lattice = AssumptionsLattice(_assumptions, bias=True)
        strategy = LinearElimination(self.control)

        algorithm = MARCO(lattice, strategy)

        for type_, set_ in algorithm:
            if type_ == "mus":
                yield self._build_unsatisfiable_subset(set_, minimal=True)

    def mus_to_string(
        self,
        mus: Iterable[tuple[clingo.Symbol, bool] | int],
        literal_lookup: dict[int, clingo.Symbol] | None = None,
    ) -> set[str]:
        """
        Converts a MUS into a set containing the string representations of the contained assumptions
        """
        # take class literal_lookup as default if no other is provided
        if literal_lookup is None:
            literal_lookup = self.literal_lookup

        mus_string = set()
        for a in mus:
            if isinstance(a, int):
                mus_string.add(str(literal_lookup[a]))  # nocoverage
            else:
                mus_string.add(str(a[0]))
        return mus_string
