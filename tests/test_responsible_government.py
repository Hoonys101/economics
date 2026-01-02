import unittest
from unittest.mock import Mock, MagicMock
from simulation.agents.government import Government
from simulation.core_agents import Household

class TestResponsibleGovernment(unittest.TestCase):
    def setUp(self):
        self.config_mock = Mock()
        self.config_mock.SURVIVAL_COST = 10.0
        self.config_mock.UNEMPLOYMENT_BENEFIT_RATIO = 0.7
        # Bracket 1 (index 1) is 5%, Bracket 2 (index 2) is 10%
        self.config_mock.TAX_BRACKETS = [(0.5, 0.0), (1.0, 0.05), (3.0, 0.10), (float('inf'), 0.20)]
        self.config_mock.TAX_MODE = "PROGRESSIVE"
        self.config_mock.INCOME_TAX_RATE = 0.2

        self.gov = Government(id=999, initial_assets=10000.0, config_module=self.config_mock)
        self.gov.gdp_history = [100.0, 110.0] # 10% Growth

    def test_approval_rating_logic(self):
        # Create households with different states
        h1 = Mock(spec=Household)
        h1.is_active = True
        h1.is_employed = True
        h1.assets = 1000.0
        h1.current_wage = 20.0
        h1.personality = "SOCIAL"

        h2 = Mock(spec=Household)
        h2.is_active = True
        h2.is_employed = False
        h2.assets = 10.0
        h2.current_wage = 0.0
        h2.personality = "MISER"

        households = [h1, h2]

        rating = self.gov.calculate_approval_rating(households)

        print(f"Approval Rating: {rating}")
        self.assertTrue(0.0 <= rating <= 1.0)

    def test_fiscal_policy_dividend(self):
        # High cash, low inflation -> Should distribute
        self.gov.assets = 10000.0
        current_gdp = 1000.0
        target = current_gdp * 0.10 # 100.0
        excess = 10000.0 - 100.0 # 9900.0
        expected_payout = excess * 0.3 # 2970.0

        h1 = Mock(spec=Household)
        h1.is_active = True
        h1.is_employed = True
        h1.assets = 0.0
        h1.id = 1
        h1.personality = "SOCIAL"

        households = [h1]

        self.gov.adjust_fiscal_policy(households, current_gdp, inflation_rate=0.02)

        # Check if dividend distributed
        self.assertAlmostEqual(h1.assets, expected_payout, delta=1.0)
        self.assertAlmostEqual(self.gov.assets, 10000.0 - expected_payout, delta=1.0)

    def test_fiscal_policy_inflation_stop(self):
        # High cash, HIGH inflation -> Should NOT distribute
        self.gov.assets = 10000.0
        current_gdp = 1000.0

        h1 = Mock(spec=Household)
        h1.is_active = True
        h1.is_employed = True
        h1.assets = 0.0
        h1.id = 1
        h1.personality = "SOCIAL"

        self.gov.adjust_fiscal_policy([h1], current_gdp, inflation_rate=0.06) # 6% inflation

        self.assertEqual(h1.assets, 0.0)

    def test_tax_adjustment_low_approval(self):
        # Force low approval
        # We need to mock calculate_approval_rating logic or ensure it returns low.
        # But adjust_fiscal_policy calls it internally.
        # Let's mock the method on the instance.
        self.gov.calculate_approval_rating = Mock(return_value=0.20) # 20% Approval
        self.gov.approval_rating = 0.20

        initial_tax = self.gov.income_tax_rate
        initial_brackets = [r for t, r in self.gov.tax_brackets]

        self.gov.adjust_fiscal_policy([], 100.0, 0.0)

        # Check if tax rate decreased
        self.assertLess(self.gov.income_tax_rate, initial_tax)

        # Check higher bracket (index 2: 10% -> should become 9%)
        # Index 1 was 5%, limited at 5%, so it stayed same.
        self.assertLess(self.gov.tax_brackets[2][1], initial_brackets[2])

if __name__ == '__main__':
    unittest.main()
