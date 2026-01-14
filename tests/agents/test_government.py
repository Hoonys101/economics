import unittest
from unittest.mock import patch, MagicMock, Mock
from simulation.agents.government import Government

class TestGovernmentDelegation(unittest.TestCase):

    def setUp(self):
        self.tax_agency_patcher = patch('simulation.agents.government.TaxAgency')
        self.education_ministry_patcher = patch('simulation.agents.government.MinistryOfEducation')

        self.MockTaxAgency = self.tax_agency_patcher.start()
        self.MockMinistryOfEducation = self.education_ministry_patcher.start()

        self.mock_tax_agency_instance = self.MockTaxAgency.return_value
        self.mock_education_ministry_instance = self.MockMinistryOfEducation.return_value

        self.mock_config = Mock()
        self.mock_config.GOVERNMENT_POLICY_MODE = "TAYLOR_RULE"
        self.mock_config.TICKS_PER_YEAR = 100
        self.mock_config.INCOME_TAX_RATE = 0.1 # This is the initial rate
        self.mock_config.CORPORATE_TAX_RATE = 0.2
        self.mock_config.TAX_MODE = "PROGRESSIVE"

        self.government = Government(id=1, initial_assets=100000, config_module=self.mock_config)
        # Manually set a different tax rate on the government instance to test that
        # the *current* rate is passed, not the initial config rate.
        self.government.income_tax_rate = 0.15
        self.government.corporate_tax_rate = 0.25

    def tearDown(self):
        self.tax_agency_patcher.stop()
        self.education_ministry_patcher.stop()

    def test_calculate_income_tax_delegation(self):
        income = 50000
        survival_cost = 15000

        self.government.calculate_income_tax(income, survival_cost)

        self.mock_tax_agency_instance.calculate_income_tax.assert_called_once_with(
            income,
            survival_cost,
            self.government.income_tax_rate, # Should pass the current rate (0.15)
            "PROGRESSIVE"
        )

    def test_calculate_corporate_tax_delegation(self):
        profit = 100000

        self.government.calculate_corporate_tax(profit)

        self.mock_tax_agency_instance.calculate_corporate_tax.assert_called_once_with(
            profit,
            self.government.corporate_tax_rate # Should pass the current rate (0.25)
        )

    def test_collect_tax_delegation(self):
        """Test if collect_tax delegates to TaxAgency."""
        # This test doesn't need changes as the signature of collect_tax was not modified
        amount = 1000
        tax_type = 'income'
        source_id = 101
        current_tick = 50

        self.government.collect_tax(amount, tax_type, source_id, current_tick)

        self.mock_tax_agency_instance.collect_tax.assert_called_once_with(self.government, amount, tax_type, source_id, current_tick)

    def test_run_public_education_delegation(self):
        """Test if run_public_education delegates to MinistryOfEducation."""
        # This test doesn't need changes either
        mock_agent1 = Mock()
        mock_agent1.education_level = 1
        agents = [mock_agent1]

        self.government.run_public_education(agents, self.mock_config, 100, None)

        self.mock_education_ministry_instance.run_public_education.assert_called_once()


class TestDeficitSpending(unittest.TestCase):
    def setUp(self):
        self.mock_config = Mock()
        self.mock_config.GOVERNMENT_POLICY_MODE = "TAYLOR_RULE"
        self.mock_config.TICKS_PER_YEAR = 100
        self.mock_config.DEFICIT_SPENDING_ENABLED = True
        self.mock_config.DEFICIT_SPENDING_LIMIT_RATIO = 0.30

        self.government = Government(id=1, initial_assets=1000, config_module=self.mock_config)

        # Mock sensory data for GDP
        self.mock_sensory_data = Mock()
        self.mock_sensory_data.current_gdp = 10000
        self.government.sensory_data = self.mock_sensory_data

    def test_deficit_spending_allowed_within_limit(self):
        """Test that the government can spend more than its assets, creating debt."""
        self.government.assets = 100
        target_agent = Mock()
        target_agent.assets = 0

        # Debt limit = 10000 * 0.30 = 3000
        # Spending 500 will result in assets of -400, which is within the limit
        amount_paid = self.government.provide_subsidy(target_agent, 500, current_tick=1)

        self.assertEqual(amount_paid, 500)
        self.assertEqual(self.government.assets, -400)
        self.assertEqual(target_agent.assets, 500)

        # Finalize tick to update debt
        self.government.finalize_tick(1)
        self.assertEqual(self.government.total_debt, 400)

    def test_deficit_spending_blocked_beyond_limit(self):
        """Test that spending is blocked when it would exceed the debt/GDP limit."""
        self.government.assets = -2900 # Already near the debt limit
        target_agent = Mock()
        target_agent.assets = 0

        # Debt limit = 10000 * 0.30 = 3000
        # Current debt is 2900. Spending another 200 would make debt 3100, exceeding the limit.
        amount_paid = self.government.provide_subsidy(target_agent, 200, current_tick=1)

        self.assertEqual(amount_paid, 0)
        self.assertEqual(self.government.assets, -2900) # Assets should not change
        self.assertEqual(target_agent.assets, 0)

        # Finalize tick to update debt
        self.government.finalize_tick(1)
        self.assertEqual(self.government.total_debt, 2900)


if __name__ == '__main__':
    unittest.main()
