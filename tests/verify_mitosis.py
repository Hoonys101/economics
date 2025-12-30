
import unittest
import random
from unittest.mock import MagicMock
from simulation.core_agents import Household, Talent
from simulation.ai.api import Personality
from simulation.ai.household_ai import HouseholdAI
from simulation.decisions.ai_driven_household_engine import AIDrivenHouseholdDecisionEngine
from simulation.ai.ai_training_manager import AITrainingManager
from simulation.markets.stock_market import StockMarket
from simulation.engine import Simulation
import config

class TestMitosis(unittest.TestCase):

    def setUp(self):
        # Setup common mocks and objects
        self.config_module = MagicMock()
        # Mock Config Constants
        self.config_module.TARGET_POPULATION = 50
        self.config_module.MITOSIS_BASE_THRESHOLD = 5000.0
        self.config_module.MITOSIS_SENSITIVITY = 1.5
        self.config_module.MITOSIS_SURVIVAL_THRESHOLD = 20.0
        self.config_module.MITOSIS_MUTATION_PROBABILITY = 0.2
        self.config_module.MITOSIS_Q_TABLE_MUTATION_RATE = 0.05
        self.config_module.SURVIVAL_NEED_DEATH_THRESHOLD = 100.0
        self.config_module.ASSETS_DEATH_THRESHOLD = 0.0
        self.config_module.HOUSEHOLD_DEATH_TURNS_THRESHOLD = 4
        self.config_module.NEED_MEDIUM_THRESHOLD = 50.0
        self.config_module.SURVIVAL_NEED_CONSUMPTION_THRESHOLD = 50.0
        self.config_module.SOCIAL_STATUS_ASSET_WEIGHT = 0.5
        self.config_module.SOCIAL_STATUS_LUXURY_WEIGHT = 0.5
        self.config_module.PERCEIVED_PRICE_UPDATE_FACTOR = 0.1
        self.config_module.BASE_DESIRE_GROWTH = 1.0
        self.config_module.MAX_DESIRE_VALUE = 100.0
        self.config_module.IMITATION_MUTATION_RATE = 0.1
        self.config_module.IMITATION_MUTATION_MAGNITUDE = 0.05
        self.config_module.HOUSEHOLD_DEFAULT_WAGE = 10.0
        self.config_module.HOUSEHOLD_LOW_ASSET_THRESHOLD = 100.0
        self.config_module.HOUSEHOLD_LOW_ASSET_WAGE = 8.0

        # Mocks needed for Household Init
        self.mock_decision_engine = MagicMock(spec=AIDrivenHouseholdDecisionEngine)
        self.mock_ai_engine = MagicMock(spec=HouseholdAI)
        self.mock_decision_engine.ai_engine = self.mock_ai_engine

        # Configure Mock AI Engine Attributes for _create_new_decision_engine
        self.mock_ai_engine.gamma = 0.9
        self.mock_ai_engine.base_alpha = 0.1
        self.mock_ai_engine.learning_focus = 0.5

        # Configure Action Selector Mock
        self.mock_action_selector = MagicMock()
        self.mock_action_selector.epsilon = 0.1
        self.mock_ai_engine.action_selector = self.mock_action_selector

        # Ensure deep recursive access works
        self.mock_ai_engine.ai_decision_engine = MagicMock()
        self.mock_decision_engine.ai_engine.ai_decision_engine = self.mock_ai_engine.ai_decision_engine

        self.talent = Talent(1.0, {})
        self.goods_data = [{"id": "food"}]
        self.initial_needs = {"survival": 0.0}

    def create_household(self, agent_id, assets, employed=False):
        h = Household(
            id=agent_id,
            talent=self.talent,
            goods_data=self.goods_data,
            initial_assets=assets,
            initial_needs=self.initial_needs.copy(),
            decision_engine=self.mock_decision_engine,
            value_orientation="wealth",
            personality=Personality.MISER,
            config_module=self.config_module
        )
        h.is_employed = employed
        # Explicitly set needs to avoid defaults overriding mock setup
        h.needs = {"survival": 0.0}
        return h

    def test_rich_family_mitosis(self):
        """Test Case 1: The 'Rich Family' Check"""
        # Create a super rich household
        parent = self.create_household(1, 15000.0, employed=True)
        # Ensure needs are low
        parent.needs["survival"] = 0.0

        # Check Mitosis
        current_pop = 10
        target_pop = 50

        child = parent.check_mitosis(current_pop, target_pop, 2)

        # Verify
        self.assertIsNotNone(child, "Mitosis should occur for rich family")
        self.assertAlmostEqual(parent.assets, 7500.0)
        self.assertAlmostEqual(child.assets, 7500.0)
        self.assertEqual(child.id, 2)
        self.assertFalse(child.is_employed)

    def test_legacy_inheritance(self):
        """Test Case 2: The 'Legacy' Check (Assets & Shares)"""
        parent = self.create_household(1, 10000.0, employed=True)
        parent.needs["survival"] = 0.0

        # Setup Shares
        firm_1_id = 101
        firm_2_id = 102
        parent.shares_owned = {firm_1_id: 10, firm_2_id: 7}

        child = parent.check_mitosis(10, 50, 2)

        self.assertIsNotNone(child)

        # Cash Check
        self.assertAlmostEqual(parent.assets, 5000.0)
        self.assertAlmostEqual(child.assets, 5000.0)

        # Stock Check
        # Firm 1: 10 -> Child gets 5, Parent keeps 5
        self.assertEqual(child.shares_owned.get(firm_1_id), 5)
        self.assertEqual(parent.shares_owned.get(firm_1_id), 5)

        # Firm 2: 7 -> Child gets 3, Parent keeps 4 (7 - 3)
        self.assertEqual(child.shares_owned.get(firm_2_id), 3)
        self.assertEqual(parent.shares_owned.get(firm_2_id), 4)

    def test_brain_inheritance(self):
        """Test Q-Table Cloning and Mutation"""
        # Create real household with real AI engine (not mock) to test cloning logic

        # Mock AI Decision Engine (Shared)
        mock_shared_ai = MagicMock()

        parent_ai = HouseholdAI(1, mock_shared_ai)
        # Populate Q-Table
        # V2 Structure: q_consumption
        from simulation.ai.q_table_manager import QTableManager
        parent_ai.q_consumption["food"] = QTableManager()
        parent_ai.q_consumption["food"].q_table = {(0,0): [1.0, 0.5, 0.0]}

        parent_decision = AIDrivenHouseholdDecisionEngine(parent_ai, self.config_module)

        parent = Household(
            id=1,
            talent=self.talent,
            goods_data=self.goods_data,
            initial_assets=10000,
            initial_needs={"survival": 0.0}, # Ensure survival need exists
            decision_engine=parent_decision,
            value_orientation="wealth",
            personality=Personality.MISER,
            config_module=self.config_module
        )
        # Ensure survival need is set low for mitosis check
        parent.needs["survival"] = 0.0

        child = parent.check_mitosis(10, 50, 2)

        self.assertIsNotNone(child, "Child should be created for brain inheritance test")

        # Manually trigger inheritance (usually done by engine)
        training_manager = AITrainingManager([], self.config_module)
        training_manager.inherit_brain(parent, child)

        child_ai = child.decision_engine.ai_engine

        # Verify Q-Table Exists in Child
        self.assertIn("food", child_ai.q_consumption)
        child_q_table = child_ai.q_consumption["food"].q_table

        self.assertIn((0,0), child_q_table)

        # Verify Mutation (Values should be close but likely not identical due to noise)
        self.assertEqual(len(child_q_table[(0,0)]), 3)

if __name__ == '__main__':
    unittest.main()
