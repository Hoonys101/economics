import unittest
from unittest.mock import MagicMock, patch
from simulation.ai.government_ai import GovernmentAI
from modules.government.ai.api import AIConfigDTO
from modules.government.dtos import GovernmentStateDTO, GovernmentPolicyDTO, GovernmentSensoryDTO

class TestGovernmentAILogic(unittest.TestCase):
    def setUp(self):
        self.mock_agent = MagicMock()
        self.mock_agent.id = "gov_test"

        # AI Config
        self.config = AIConfigDTO(
            alpha=0.1,
            gamma=0.95,
            epsilon=0.1,
            w_approval=0.7,
            w_stability=0.2,
            w_lobbying=0.1,
            lobbying_threshold_high_tax=0.25,
            lobbying_threshold_high_unemployment=0.05
        )

        self.ai = GovernmentAI(self.mock_agent, self.config)

    def _create_state_dto(self, inflation=0.02, unemployment=0.04, gdp_growth=0.0,
                          current_gdp=1000.0, total_debt=60000, approval=0.5,
                          corp_tax=0.2):
        """Helper to create DTO"""
        sensory = MagicMock(spec=GovernmentSensoryDTO)
        sensory.inflation_sma = inflation
        sensory.unemployment_sma = unemployment
        sensory.gdp_growth_sma = gdp_growth
        sensory.current_gdp = current_gdp
        sensory.approval_sma = approval

        # total_debt in pennies. 60000 = $600.

        return GovernmentStateDTO(
            tick=1,
            assets={},
            total_debt=total_debt,
            income_tax_rate=0.2,
            corporate_tax_rate=corp_tax,
            policy=GovernmentPolicyDTO(),
            approval_rating=approval,
            sensory_data=sensory
        )

    def test_get_state_ideal(self):
        """Test State Discretization for Ideal Conditions (6-tuple)"""
        # Inf=0.02 (Target) -> 1
        # Unemp=0.04 (Target) -> 1
        # GDP=0.0 (Stagnant/Normal) -> 1
        # Debt=$600/$1000=0.6 -> Safe (1)
        # Approval=0.5 -> Safe (1)
        # Lobbying: Unemp=0.04(<0.05), Tax=0.2(<0.25) -> Neutral (0)

        dto = self._create_state_dto()
        expected_state = (1, 1, 1, 1, 1, 0)
        state = self.ai._get_state(dto)
        self.assertEqual(state, expected_state)

    def test_lobbying_logic(self):
        # 1. Corp Pressure (High Tax)
        dto_corp = self._create_state_dto(corp_tax=0.30)
        state_corp = self.ai._get_state(dto_corp)
        self.assertEqual(state_corp[5], 1) # Lobbying=1 (Corp)

        # 2. Labor Pressure (High Unemployment)
        dto_labor = self._create_state_dto(unemployment=0.10)
        state_labor = self.ai._get_state(dto_labor)
        self.assertEqual(state_labor[5], 2) # Lobbying=2 (Labor)

        # 3. Priority (Both High) -> Labor wins (Unemployment is crisis)
        dto_both = self._create_state_dto(corp_tax=0.30, unemployment=0.10)
        state_both = self.ai._get_state(dto_both)
        self.assertEqual(state_both[5], 2)

    def test_populist_reward(self):
        """Test Reward Function Calculation"""
        # Scenario:
        # Approval = 0.4 (Low) -> R_app = (0.4-0.5)*100 = -10.
        # Stability: Inf=0.02(Ideal), Unemp=0.04(Ideal) -> R_stab = 0.
        # Lobbying: Neutral.

        # Total = 0.7 * (-10) + 0.2 * 0 = -7.0

        dto = self._create_state_dto(approval=0.4)
        reward = self.ai.calculate_reward(dto)
        self.assertAlmostEqual(reward, -7.0)

        # Scenario: Crisis but Popular
        # Approval = 0.8 -> R_app = 30.
        # Stability: Inf=0.05 (+0.03), Unemp=0.04.
        # R_stab = - ((0.03^2 + 0) * 50) = - (0.0009 * 50) = -0.045.

        # Total = 0.7 * 30 + 0.2 * (-0.045) = 21 - 0.009 = 20.991

        dto_populist = self._create_state_dto(approval=0.8, inflation=0.05)
        reward_pop = self.ai.calculate_reward(dto_populist)
        self.assertAlmostEqual(reward_pop, 20.991)

    def test_lobbying_bonus(self):
        # Setup previous state: Lobbying = Corp (1)
        self.ai.last_state = (1, 1, 1, 1, 1, 1)
        # Setup previous action: Fiscal Ease (3)
        self.ai.last_action_idx = self.ai.ACTION_FISCAL_EASE

        # Current state doesn't matter for lobbying bonus part,
        # but needed for base reward.
        # Let's make base reward 0 (Ideal state).
        dto = self._create_state_dto() # Approval 0.5 -> R_app 0. Stability 0.

        # Reward = 0 + 0 + 0.1 * 10 = 1.0
        reward = self.ai.calculate_reward(dto)
        self.assertAlmostEqual(reward, 1.0)

        # Test No Bonus (Action Mismatch)
        self.ai.last_action_idx = self.ai.ACTION_HAWKISH
        reward_no_bonus = self.ai.calculate_reward(dto)
        self.assertAlmostEqual(reward_no_bonus, 0.0)

if __name__ == '__main__':
    unittest.main()
