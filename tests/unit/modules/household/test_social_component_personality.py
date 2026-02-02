import unittest
from unittest.mock import MagicMock
from simulation.ai.enums import Personality
from modules.household.dtos import SocialStateDTO
from modules.household.social_component import SocialComponent
from simulation.dtos.config_dtos import HouseholdConfigDTO
from simulation.dtos.api import MacroFinancialContext

class TestSocialComponentPersonality(unittest.TestCase):
    def setUp(self):
        self.component = SocialComponent()

        # Mock Config
        self.config = MagicMock(spec=HouseholdConfigDTO)
        self.config.personality_status_seeker_wealth_pct = 0.9
        self.config.personality_survival_mode_wealth_pct = 0.2
        self.config.desire_weights_map = {
            "STATUS_SEEKER": {"survival": 1.0, "social": 1.5},
            "SURVIVAL_MODE": {"survival": 2.0, "social": 0.1},
            "BALANCED": {"survival": 1.0, "social": 1.0}
        }

        # Base Social State
        self.social_state = SocialStateDTO(
            personality=Personality.BALANCED,
            social_status=0.0,
            discontent=0.0,
            approval_rating=1,
            conformity=0.5,
            social_rank=0.5,
            quality_preference=0.5,
            brand_loyalty={},
            last_purchase_memory={},
            patience=0.5,
            optimism=0.5,
            ambition=0.5,
            last_leisure_type="IDLE",
            desire_weights={"survival": 1.0, "social": 1.0}
        )

        # Base Econ State (Mock)
        self.econ_state = MagicMock() # Not used in logic yet

    def test_update_status_seeker(self):
        # 95th Percentile -> Should become STATUS_SEEKER
        agent_id = 1
        macro_context = MacroFinancialContext(
            inflation_rate=0.0, gdp_growth_rate=0.0, market_volatility=0.0, interest_rate_trend=0.0,
            wealth_percentiles={agent_id: 0.95}
        )

        updated_state = self.component.update_dynamic_personality(
            agent_id, self.social_state, self.econ_state, macro_context, self.config
        )

        self.assertEqual(updated_state.personality, Personality.STATUS_SEEKER)
        self.assertEqual(updated_state.desire_weights["social"], 1.5)

    def test_update_survival_mode(self):
        # 15th Percentile -> Should become SURVIVAL_MODE
        agent_id = 2
        macro_context = MacroFinancialContext(
            inflation_rate=0.0, gdp_growth_rate=0.0, market_volatility=0.0, interest_rate_trend=0.0,
            wealth_percentiles={agent_id: 0.15}
        )

        updated_state = self.component.update_dynamic_personality(
            agent_id, self.social_state, self.econ_state, macro_context, self.config
        )

        self.assertEqual(updated_state.personality, Personality.SURVIVAL_MODE)
        self.assertEqual(updated_state.desire_weights["survival"], 2.0)
        self.assertEqual(updated_state.desire_weights["social"], 0.1)

    def test_no_change(self):
        # 50th Percentile -> Should remain BALANCED
        agent_id = 3
        macro_context = MacroFinancialContext(
            inflation_rate=0.0, gdp_growth_rate=0.0, market_volatility=0.0, interest_rate_trend=0.0,
            wealth_percentiles={agent_id: 0.50}
        )

        updated_state = self.component.update_dynamic_personality(
            agent_id, self.social_state, self.econ_state, macro_context, self.config
        )

        self.assertEqual(updated_state.personality, Personality.BALANCED)
        self.assertEqual(updated_state.desire_weights["social"], 1.0)

if __name__ == '__main__':
    unittest.main()
