"""
This module serves as the public API for the simulation package.
It re-exports core classes and functions from various sub-modules,
providing a centralized and clear interface for external interaction.
"""

from .core_markets import Market
from .engine import Simulation, EconomicIndicatorTracker
from .core_agents import Household, Talent, Skill
from .firms import Firm
from .decisions.action_proposal import ActionProposalEngine
from .decisions.base_decision_engine import BaseDecisionEngine
from .decisions.firm_decision_engine import FirmDecisionEngine
from .decisions.household_decision_engine import HouseholdDecisionEngine
from .ai.api import (
    AITrainingManager,
    AIDecisionEngine,
    AIEngineRegistry,
    StateBuilder,
    ModelWrapper,
    RewardCalculator
)

__all__ = [
    "Market",
    "Simulation",
    "EconomicIndicatorTracker",
    "Household",
    "Talent",
    "Skill",
    "Firm",
    "ActionProposalEngine",
    "BaseDecisionEngine",
    "FirmDecisionEngine",
    "HouseholdDecisionEngine",
    "AITrainingManager",
    "AIDecisionEngine",
    "AIEngineRegistry",
    "StateBuilder",
    "ModelWrapper",
    "RewardCalculator"
]
