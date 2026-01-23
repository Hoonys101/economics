import unittest
from unittest.mock import MagicMock
from simulation.core_agents import Household, Talent
from simulation.ai.api import Personality
from simulation.decisions.base_decision_engine import BaseDecisionEngine
from simulation.ai.household_ai import HouseholdAI
import config


class TestSystem2Integration(unittest.TestCase):
    def setUp(self):
        # Mock Engine & AI
        self.mock_decision_engine = MagicMock(spec=BaseDecisionEngine)
        self.mock_ai = HouseholdAI("test_agent", self.mock_decision_engine)
        self.mock_decision_engine.ai_engine = self.mock_ai
        self.mock_decision_engine.config_module = config
        self.mock_ai.ai_decision_engine = self.mock_decision_engine  # Circular ref

        self.agent = Household(
            id=1,
            talent=Talent(0.1, {}),
            goods_data=[],
            initial_assets=1000.0,
            initial_needs={},
            decision_engine=self.mock_decision_engine,
            value_orientation="wealth_and_needs",
            personality=Personality.CONSERVATIVE,
            config_module=config,
        )
        self.agent.expected_wage = 10.0  # $10/hr

        # Override config constants for deterministic testing
        config.HOUSEWORK_BASE_HOURS = 4.0
        config.CHILDCARE_TIME_REQUIRED = 8.0
        config.FORMULA_TECH_LEVEL = 0.0

    def test_male_vs_female_npv_gap(self):
        """
        Verify that Female agent with child has lower NPV than Male with child
        under 'Dark Ages' conditions (No Tech).
        """
        # Common setup: 1 child, Spouse exists
        self.agent.children_ids = [100]  # 1 child
        self.agent.spouse_id = 99
        market_data = {"goods_market": {"basic_food_current_sell_price": 5.0}}

        # 1. Male Projection
        self.agent.gender = "M"
        # Clear Cache
        self.agent.system2_planner.cached_projection = {}
        self.agent.system2_planner.last_calc_tick = -999
        res_m = self.agent.system2_planner.project_future(0, market_data)
        npv_m = res_m["npv_wealth"]

        # 2. Female Projection
        self.agent.gender = "F"
        # Clear Cache
        self.agent.system2_planner.cached_projection = {}
        self.agent.system2_planner.last_calc_tick = -999
        res_f = self.agent.system2_planner.project_future(0, market_data)
        npv_f = res_f["npv_wealth"]

        print(f"NPV Male: {npv_m:.2f}")
        print(f"NPV Female: {npv_f:.2f}")

        # Logic Check:
        # Male: Housework(2.0 shared) + Childcare(0.0) = 2.0 Obligation
        #       Work Cap = 14 - 2 = 12 -> 8h work. Full Income.
        # Female: Housework(2.0 shared) + Childcare(8.0) = 10.0 Obligation
        #         Work Cap = 14 - 10 = 4h. Half Income.

        self.assertGreater(
            npv_m,
            npv_f * 1.5,
            "Male NPV should be significantly higher due to Lactation Lock",
        )

    def test_tech_liberation(self):
        """
        Verify that Formula Tech restores Female NPV.
        """
        self.agent.children_ids = [100]
        self.agent.spouse_id = 99
        self.agent.gender = "F"
        market_data = {"goods_market": {"basic_food_current_sell_price": 5.0}}

        # 1. Dark Ages
        config.FORMULA_TECH_LEVEL = 0.0
        # Clear Cache
        self.agent.system2_planner.cached_projection = {}
        self.agent.system2_planner.last_calc_tick = -999
        res_dark = self.agent.system2_planner.project_future(0, market_data)

        # 2. Tech Revolution
        config.FORMULA_TECH_LEVEL = 1.0
        # Clear Cache
        self.agent.system2_planner.cached_projection = {}
        self.agent.system2_planner.last_calc_tick = -999
        res_light = self.agent.system2_planner.project_future(0, market_data)

        print(f"NPV Dark Ages: {res_dark['npv_wealth']:.2f}")
        print(f"NPV Revolution: {res_light['npv_wealth']:.2f}")

        self.assertGreater(
            res_light["npv_wealth"],
            res_dark["npv_wealth"],
            "Tech should improve Female NPV",
        )


if __name__ == "__main__":
    unittest.main()
