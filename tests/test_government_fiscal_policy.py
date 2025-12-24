import unittest
import logging
import sys
import os

# Ensure we can import from the root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.engine import Simulation
from simulation.core_agents import Household, Talent
from simulation.firms import Firm
from simulation.ai_model import AIEngineRegistry
from simulation.ai.state_builder import StateBuilder
from simulation.decisions.action_proposal import ActionProposalEngine
from simulation.decisions.ai_driven_firm_engine import AIDrivenFirmDecisionEngine
from simulation.decisions.ai_driven_household_engine import AIDrivenHouseholdDecisionEngine
from simulation.ai.api import Personality
from simulation.ai.household_ai import HouseholdAI
from simulation.ai.firm_ai import FirmAI
from simulation.db.repository import SimulationRepository
import config as cfg

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(name)s:%(message)s')
logger = logging.getLogger("TestGov")

class TestGovernmentFiscalPolicy(unittest.TestCase):
    def setUp(self):
        self.repository = SimulationRepository()
        self.state_builder = StateBuilder()
        self.action_proposal_engine = ActionProposalEngine(config_module=cfg)
        self.ai_trainer = AIEngineRegistry(
            action_proposal_engine=self.action_proposal_engine,
            state_builder=self.state_builder
        )

    def tearDown(self):
        self.repository.close()

    def _create_household(self, id: int, assets: float):
        value_orientation = "wealth_and_needs"
        ai_engine = self.ai_trainer.get_engine(value_orientation)
        household_ai = HouseholdAI(agent_id=id, ai_decision_engine=ai_engine)
        decision_engine = AIDrivenHouseholdDecisionEngine(
            ai_engine=household_ai, config_module=cfg
        )
        return Household(
            id=id,
            talent=Talent(1.0, {}),
            goods_data=[{"id": "basic_food", "utility_effects": {"survival": 10.0}}],
            initial_assets=assets,
            initial_needs={"survival": 30.0, "social": 20.0, "improvement": 10.0, "asset": 10.0},
            decision_engine=decision_engine,
            value_orientation=value_orientation,
            personality=Personality.MISER,
            config_module=cfg,
            logger=logger,
        )

    def _create_firm(self, id: int, assets: float):
        value_orientation = "profit_maximizer"
        ai_engine = self.ai_trainer.get_engine(value_orientation)
        firm_ai = FirmAI(agent_id=id, ai_decision_engine=ai_engine)
        decision_engine = AIDrivenFirmDecisionEngine(
            ai_engine=firm_ai, config_module=cfg
        )
        return Firm(
            id=id,
            initial_capital=assets,
            initial_liquidity_need=10.0,
            specialization="basic_food",
            productivity_factor=10.0,
            decision_engine=decision_engine,
            value_orientation=value_orientation,
            config_module=cfg,
            logger=logger,
        )

    def test_tax_collection_and_subsidies(self):
        h1 = self._create_household(1, 1000.0)
        f1 = self._create_firm(101, 5000.0)
        
        sim = Simulation(
            households=[h1],
            firms=[f1],
            ai_trainer=self.ai_trainer,
            repository=self.repository,
            config_module=cfg,
            goods_data=[{"id": "basic_food", "name": "Basic Food"}]
        )
        
        gov = sim.government
        initial_gov_assets = gov.assets
        
        # 1. Manual Tax Collection Test
        gov.collect_tax(100.0, "test_tax", 1, 1)
        self.assertEqual(gov.assets, initial_gov_assets + 100.0)
        self.assertEqual(gov.total_collected_tax, 100.0)
        
        # 2. Subsidy Test
        firm = sim.firms[0]
        initial_firm_assets = firm.assets
        gov.provide_subsidy(firm, 50.0, 1)
        self.assertEqual(gov.assets, initial_gov_assets + 50.0)
        self.assertEqual(firm.assets, initial_firm_assets + 50.0)
        self.assertEqual(gov.total_spent_subsidies, 50.0)

    def test_infrastructure_investment_and_tfp_boost(self):
        h1 = self._create_household(1, 1000.0)
        f1 = self._create_firm(101, 5000.0)
        
        sim = Simulation(
            households=[h1],
            firms=[f1],
            ai_trainer=self.ai_trainer,
            repository=self.repository,
            config_module=cfg,
            goods_data=[{"id": "basic_food", "name": "Basic Food"}]
        )
        
        gov = sim.government
        gov.assets = 6000.0 # Enough for investment (Cost=5000)
        
        initial_tfp = sim.firms[0].productivity_factor
        
        # Engine integration test via run_tick
        # Before run_tick, we need to make sure some taxes are collected or gov has enough assets
        sim.run_tick() # This will call government.invest_infrastructure if assets >= cost
        
        # Check if TFP increased
        new_tfp = sim.firms[0].productivity_factor
        self.assertGreater(new_tfp, initial_tfp)
        logger.info(f"✓ Global TFP Boost verified: {initial_tfp} -> {new_tfp}")

if __name__ == "__main__":
    unittest.main()

if __name__ == "__main__":
    unittest.main()
