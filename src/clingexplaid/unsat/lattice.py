"""Wrappers for the musclingo lattice classes."""

from abc import ABC, abstractmethod

from musclingo.lattice import AssumptionsLattice, Lattice


class LatticeFactory(ABC):
    """Factory for creating Lattice instances."""

    @abstractmethod
    def __init__(self) -> None: ...

    @abstractmethod
    def new(self, literals: set[int]) -> Lattice:
        """
        Create a new Lattice instance.

        Parameters
        ----------
        literals
            A list of literals to use for the lattice.

        Returns
        -------
            A new Lattice instance.
        """


class AssumptionLatticeFactory(LatticeFactory):
    """Factory for creating AssumptionLattice instances."""

    def __init__(self, bias: bool) -> None:
        super().__init__()
        self._bias = bias

    def new(self, literals: set[int]) -> AssumptionsLattice:
        """
        Create a new AssumptionLattice instance.

        Parameters
        ----------
        literals
            A list of literals to use for the lattice.

        Returns
        -------
            A new AssumptionLattice instance.
        """
        lattice = AssumptionsLattice(literals, self._bias)
        return lattice
