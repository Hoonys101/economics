
import unittest
import math
from unittest.mock import MagicMock
from simulation.core_agents import Household, Talent
from simulation.ai.api import Personality
from simulation.ai.household_ai import HouseholdAI
from simulation.decisions.ai_driven_household_engine import AIDrivenHouseholdDecisionEngine
from simulation.ai.ai_training_manager import AITrainingManager
import config

class TestMaslowEducation(unittest.TestCase):

    def setUp(self):
        # Mock Config
        self.config_module = MagicMock()
        # Set values as floats, not Mocks
        self.config_module.MASLOW_SURVIVAL_THRESHOLD = 50.0
        self.config_module.EDUCATION_SENSITIVITY = 0.1
        self.config_module.BASE_LEARNING_RATE = 0.1
        self.config_module.MAX_LEARNING_RATE = 0.5
        self.config_module.LEARNING_EFFICIENCY = 1.0
        self.config_module.GOODS = {
            "food": {"utility_effects": {"survival": 10}},
            "luxury": {"utility_effects": {"social": 10}},
            "education_service": {"utility_effects": {"improvement": 10}, "is_service": True}
        }
        # Required for Engine
        self.config_module.HOUSEHOLD_MAX_PURCHASE_QUANTITY = 5.0
        self.config_module.NEED_FACTOR_BASE = 1.0
        self.config_module.NEED_FACTOR_SCALE = 100.0
        self.config_module.VALUATION_MODIFIER_BASE = 1.0
        self.config_module.VALUATION_MODIFIER_RANGE = 0.0
        self.config_module.BUDGET_LIMIT_NORMAL_RATIO = 1.0
        self.config_module.BUDGET_LIMIT_URGENT_RATIO = 1.0
        self.config_module.MIN_PURCHASE_QUANTITY = 0.1
        self.config_module.BULK_BUY_NEED_THRESHOLD = 100.0
        self.config_module.BULK_BUY_AGG_THRESHOLD = 1.0
        self.config_module.MARKET_PRICE_FALLBACK = 10.0
        self.config_module.BUDGET_LIMIT_URGENT_NEED = 80.0
        self.config_module.MITOSIS_MUTATION_PROBABILITY = 0.2
        self.config_module.IMITATION_MUTATION_RATE = 0.1
        self.config_module.MITOSIS_Q_TABLE_MUTATION_RATE = 0.05
        self.config_module.IMITATION_MUTATION_MAGNITUDE = 0.05

        # Required for Household Init
        self.config_module.BASE_DESIRE_GROWTH = 1.0
        self.config_module.MAX_DESIRE_VALUE = 100.0
        self.config_module.SOCIAL_STATUS_ASSET_WEIGHT = 0.1
        self.config_module.SOCIAL_STATUS_LUXURY_WEIGHT = 0.1
        self.config_module.NEED_MEDIUM_THRESHOLD = 50.0
        self.config_module.SURVIVAL_NEED_CONSUMPTION_THRESHOLD = 50.0
        self.config_module.HOUSEHOLD_LOW_ASSET_THRESHOLD = 100.0
        self.config_module.HOUSEHOLD_LOW_ASSET_WAGE = 8.0
        self.config_module.HOUSEHOLD_DEFAULT_WAGE = 10.0
        self.config_module.LABOR_MARKET_MIN_WAGE = 8.0
        self.config_module.JOB_QUIT_THRESHOLD_BASE = 2.0
        self.config_module.JOB_QUIT_PROB_BASE = 0.1
        self.config_module.JOB_QUIT_PROB_SCALE = 0.1
        self.config_module.RESERVATION_WAGE_BASE = 1.0
        self.config_module.RESERVATION_WAGE_RANGE = 0.5
        self.config_module.HOUSEHOLD_INVESTMENT_BUDGET_RATIO = 0.2
        self.config_module.HOUSEHOLD_MIN_ASSETS_FOR_INVESTMENT = 500.0
        self.config_module.STOCK_MARKET_ENABLED = False

        # Mock Engine & AI
        self.mock_ai_engine = MagicMock(spec=HouseholdAI)
        self.mock_ai_engine.decide_action_vector.return_value = MagicMock(
            consumption_aggressiveness={"luxury": 0.5, "food": 0.5},
            job_mobility_aggressiveness=0.5,
            work_aggressiveness=0.5,
            investment_aggressiveness=0.5
        )
        self.mock_ai_engine.action_selector = MagicMock()
        self.mock_ai_engine.action_selector.epsilon = 0.1
        self.mock_ai_engine.base_alpha = 0.1

        self.mock_decision_engine = AIDrivenHouseholdDecisionEngine(self.mock_ai_engine, self.config_module)

        self.talent = Talent(1.0, {})
        self.goods_data = [{"id": "food"}, {"id": "luxury"}, {"id": "education_service"}]

    def create_household(self, agent_id, needs):
        h = Household(
            id=agent_id,
            talent=self.talent,
            goods_data=self.goods_data,
            initial_assets=1000.0,
            initial_needs=needs,
            decision_engine=self.mock_decision_engine,
            value_orientation="wealth",
            personality=Personality.MISER,
            config_module=self.config_module
        )
        return h

    def test_maslow_gating_logic(self):
        """Test HouseholdAI decide_action_vector for Maslow Gating"""
        # We need a REAL HouseholdAI to test the gating logic inside decide_action_vector
        real_ai = HouseholdAI("test_agent", MagicMock())
        real_ai.q_consumption = {"food": MagicMock(), "luxury": MagicMock()}
        real_ai.q_investment = MagicMock()

        # Mock action selector to return specific index (e.g. 2 -> 0.5)
        real_ai.action_selector = MagicMock()
        real_ai.action_selector.choose_action.return_value = 2 # 0.5 aggressiveness

        agent_data = {"needs": {"survival": 80.0}, "assets": 1000.0} # Starving
        market_data = {}
        goods_list = ["food", "luxury"]

        # Call decide_action_vector
        vector = real_ai.decide_action_vector(
            agent_data, market_data, goods_list, self.config_module
        )

        # Food should have agg > 0 (0.5)
        self.assertEqual(vector.consumption_aggressiveness["food"], 0.5)

        # Luxury should have agg == 0.0 (Gated)
        self.assertEqual(vector.consumption_aggressiveness["luxury"], 0.0)

        # Investment should be 0.0
        self.assertEqual(vector.investment_aggressiveness, 0.0)

        # Case 2: Not Starving
        agent_data["needs"]["survival"] = 20.0
        vector_ok = real_ai.decide_action_vector(
            agent_data, market_data, goods_list, self.config_module
        )

        # Luxury should be active
        self.assertEqual(vector_ok.consumption_aggressiveness["luxury"], 0.5)
        self.assertEqual(vector_ok.investment_aggressiveness, 0.5)

    def test_education_xp_consumption(self):
        """Test XP gain on education consumption"""
        agent = self.create_household(1, {"survival": 0.0})
        agent.inventory["education_service"] = 2.0

        # Consume
        agent.consume("education_service", 1.0, 10)

        # Check XP
        # Efficiency = 1.0
        self.assertEqual(agent.education_xp, 1.0)

        # Check Inventory Decrement (standard logic)
        self.assertEqual(agent.inventory["education_service"], 1.0)

    def test_inheritance_bonus(self):
        """Test Child Base Alpha Bonus"""
        # Create Independent Engines for this test
        parent_ai = MagicMock(spec=HouseholdAI)
        parent_ai.base_alpha = 0.1
        parent_decision = MagicMock(spec=AIDrivenHouseholdDecisionEngine)
        parent_decision.ai_engine = parent_ai

        child_ai = MagicMock(spec=HouseholdAI)
        child_ai.base_alpha = 0.1
        child_decision = MagicMock(spec=AIDrivenHouseholdDecisionEngine)
        child_decision.ai_engine = child_ai

        # Create Households manually
        parent = Household(
            id=1,
            talent=self.talent,
            goods_data=self.goods_data,
            initial_assets=1000.0,
            initial_needs={},
            decision_engine=parent_decision,
            value_orientation="wealth",
            personality=Personality.MISER,
            config_module=self.config_module
        )
        parent.education_xp = 100.0

        child = Household(
            id=2,
            talent=self.talent,
            goods_data=self.goods_data,
            initial_assets=1000.0,
            initial_needs={},
            decision_engine=child_decision,
            value_orientation="wealth",
            personality=Personality.MISER,
            config_module=self.config_module
        )

        # Inherit
        manager = AITrainingManager([], self.config_module)

        # DEBUG
        print(f"DEBUG: Sensitivity={getattr(self.config_module, 'EDUCATION_SENSITIVITY', 'N/A')}")
        print(f"DEBUG: Parent XP={parent.education_xp}")
        print(f"DEBUG: Child Has AI Engine? {hasattr(child.decision_engine, 'ai_engine')}")

        manager.inherit_brain(parent, child)

        print(f"DEBUG: Child Alpha={child.decision_engine.ai_engine.base_alpha}")

        # Check Child Alpha
        # 0.1 + log1p(100)*0.1 = 0.56 -> capped 0.5
        self.assertEqual(child.decision_engine.ai_engine.base_alpha, 0.5)

        # Check Parent Alpha Unchanged
        self.assertEqual(parent.decision_engine.ai_engine.base_alpha, 0.1)

if __name__ == '__main__':
    unittest.main()
