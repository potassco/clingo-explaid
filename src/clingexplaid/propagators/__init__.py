"""
Propagators for Explanation
"""

# pragma: no cover

from typing import List

from .propagator_decision_order import DecisionOrderPropagator

DecisionLevel = List[int]
DecisionLevelList = List[DecisionLevel]

__all__ = [
    "DecisionOrderPropagator",
]
