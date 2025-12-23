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
from .decisions import BaseDecisionEngine, FirmDecisionEngine, HouseholdDecisionEngine
from .ai.ai_training_manager import AITrainingManager
from .ai_model import AIDecisionEngine, AIEngineRegistry
from .ai.state_builder import StateBuilder
from .ai.model_wrapper import ModelWrapper
from .ai.reward_calculator import RewardCalculator

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
    "RewardCalculator",
]
