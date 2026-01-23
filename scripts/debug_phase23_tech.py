import sys
import os
import logging
import json

# Setup paths
sys.path.append(os.path.abspath("."))

import config as Config
from simulation.initialization.initializer import SimulationInitializer
from simulation.db.repository import SimulationRepository
from simulation.ai.state_builder import StateBuilder
from simulation.decisions.action_proposal import ActionProposalEngine
from simulation.ai_model import AIEngineRegistry
from simulation.core_agents import Household
from simulation.firms import Firm
from simulation.core_agents import Talent
from simulation.ai.api import Personality
from simulation.decisions.rule_based_household_engine import (
    RuleBasedHouseholdDecisionEngine,
)
from simulation.decisions.standalone_rule_based_firm_engine import (
    StandaloneRuleBasedFirmDecisionEngine,
)
from modules.common.config_manager.api import ConfigManager
from unittest.mock import MagicMock

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("TechDebug")


class MockConfigManager(ConfigManager):
    def __init__(self, config_module):
        self.config = config_module

    def get(self, key, default=None):
        return getattr(self.config, key, default)


def debug_tech():
    Config.TECH_FERTILIZER_UNLOCK_TICK = 2
    repo = MagicMock(spec=SimulationRepository)
    repo.save_simulation_run.return_value = 1
    config_manager = MockConfigManager(Config)

    state_builder = StateBuilder()
    action_proposal = ActionProposalEngine(config_module=Config)
    ai_registry = AIEngineRegistry(
        action_proposal_engine=action_proposal, state_builder=state_builder
    )

    num_households = 2
    num_firms = 2

    goods_data = [
        {
            "id": "basic_food",
            "sector": "FOOD",
            "is_luxury": False,
            "utility_effects": {"survival": 10},
            "initial_price": 5.0,
        }
    ]

    households = [
        Household(
            id=i,
            initial_assets=1000,
            decision_engine=RuleBasedHouseholdDecisionEngine(Config, logger),
            config_module=Config,
            talent=Talent(1.0, {}),
            goods_data=goods_data,
            initial_needs={"survival": 50},
            value_orientation="wealth_and_needs",
            personality=Personality.CONSERVATIVE,
        )
        for i in range(num_households)
    ]

    firms = [
        Firm(
            id=1000,
            initial_capital=50000,
            initial_liquidity_need=1000,
            specialization="basic_food",
            productivity_factor=10.0,
            decision_engine=StandaloneRuleBasedFirmDecisionEngine(Config, logger),
            value_orientation="PROFIT",
            config_module=Config,
            sector="FOOD",
            is_visionary=True,
        ),
        Firm(
            id=1001,
            initial_capital=50000,
            initial_liquidity_need=1000,
            specialization="basic_food",
            productivity_factor=10.0,
            decision_engine=StandaloneRuleBasedFirmDecisionEngine(Config, logger),
            value_orientation="PROFIT",
            config_module=Config,
            sector="FOOD",
            is_visionary=False,
        ),
    ]

    initializer = SimulationInitializer(
        config_manager, Config, goods_data, repo, logger, households, firms, ai_registry
    )
    sim = initializer.build_simulation()

    print(f"--- Initial State ---")
    print(f"Firms: {[(f.id, f.sector, f.is_visionary) for f in sim.firms]}")
    print(f"Tech Tree: {sim.technology_manager.tech_tree}")

    for tick in range(1, 11):
        sim.run_tick()
        unlocked = [
            t.id for t in sim.technology_manager.tech_tree.values() if t.is_unlocked
        ]
        adopted = {
            f.id: [
                t
                for t in sim.technology_manager.tech_tree
                if sim.technology_manager.has_adopted(f.id, t)
            ]
            for f in sim.firms
        }
        print(f"Tick {tick}: Unlocked={unlocked}, Adopted={adopted}")


if __name__ == "__main__":
    debug_tech()
