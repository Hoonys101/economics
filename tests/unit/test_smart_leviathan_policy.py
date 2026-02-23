import unittest
from unittest.mock import MagicMock, call, patch
from simulation.policies.smart_leviathan_policy import SmartLeviathanPolicy
from modules.government.dtos import GovernmentStateDTO

class TestSmartLeviathanPolicy(unittest.TestCase):
    def setUp(self):
        self.mock_gov = MagicMock()
        self.mock_config = MagicMock()
        # Ensure getattr(config, "POLICY_ACTUATOR_BOUNDS") returns a dict, not a Mock
        self.mock_config.POLICY_ACTUATOR_BOUNDS = {}
        # Ensure getattr(config, "POLICY_ACTUATOR_STEP_SIZES") returns a tuple
        self.mock_config.POLICY_ACTUATOR_STEP_SIZES = (0.01, 0.0025, 0.1)
        # Ensure getattr(config, "BUDGET_ALLOCATION_MIN") returns float
        self.mock_config.BUDGET_ALLOCATION_MIN = 0.1
        self.mock_config.NORMAL_BUDGET_MULTIPLIER_CAP = 1.0

        # Mock Gov attributes for DTO construction
        self.mock_gov.assets = {}
        self.mock_gov.total_debt = 1000
        self.mock_gov.income_tax_rate = 0.2
        self.mock_gov.corporate_tax_rate = 0.2
        self.mock_gov.approval_rating = 0.5
        self.mock_gov.sensory_data = None
        self.mock_gov.ruling_party = None
        self.mock_gov.welfare_budget_multiplier = 1.0
        self.mock_gov.firm_subsidy_budget_multiplier = 1.0
        self.mock_gov.fiscal_policy = None
        self.mock_gov.policy_lockouts = {}
        self.mock_gov.gdp_history = []
        self.mock_gov.potential_gdp = 0.0
        self.mock_gov.fiscal_stance = 0.0

    def test_learning_order(self):
        """Verify update_learning is called BEFORE decide_policy"""
        current_tick = 30 # Must match default interval 30
        self.mock_config.GOV_ACTION_INTERVAL = 30

        mock_cb = MagicMock()
        mock_cb.base_rate = 0.05 # Mock float for comparison

        # Patch GovernmentAI where it is defined, so the import inside __init__ gets the mock
        with patch('simulation.ai.government_ai.GovernmentAI') as MockAI:
            policy = SmartLeviathanPolicy(self.mock_gov, self.mock_config)
            mock_ai_instance = policy.ai

            policy.decide(self.mock_gov, None, current_tick, mock_cb)

            # Get all calls to the AI instance
            calls = mock_ai_instance.method_calls

            # Filter for update_learning and decide_policy
            relevant_calls = [c[0] for c in calls if c[0] in ('update_learning', 'decide_policy')]

            # Check order
            self.assertEqual(relevant_calls, ['update_learning', 'decide_policy'])

    def test_debt_fallback(self):
        """Verify robust debt calculation"""
        current_tick = 30
        self.mock_config.GOV_ACTION_INTERVAL = 30
        mock_cb = MagicMock()
        mock_cb.base_rate = 0.05

        with patch('simulation.ai.government_ai.GovernmentAI') as MockAI:
            policy = SmartLeviathanPolicy(self.mock_gov, self.mock_config)
            mock_ai_instance = policy.ai

            # Scenario 1: total_debt exists
            self.mock_gov.total_debt = 500
            policy.decide(self.mock_gov, None, current_tick, mock_cb)
            # Check arguments passed to decide_policy
            args, _ = mock_ai_instance.decide_policy.call_args
            dto = args[1]
            self.assertEqual(dto.total_debt, 500)

            # Scenario 2: total_debt missing, negative wealth
            del self.mock_gov.total_debt
            self.mock_gov.total_wealth = -900 # 900 debt
            policy.decide(self.mock_gov, None, current_tick, mock_cb)
            args, _ = mock_ai_instance.decide_policy.call_args
            dto = args[1]
            self.assertEqual(dto.total_debt, 900)

            # Scenario 3: total_debt missing, positive wealth
            self.mock_gov.total_wealth = 5000
            policy.decide(self.mock_gov, None, current_tick, mock_cb)
            args, _ = mock_ai_instance.decide_policy.call_args
            dto = args[1]
            self.assertEqual(dto.total_debt, 0)

if __name__ == '__main__':
    unittest.main()
