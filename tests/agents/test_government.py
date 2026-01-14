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


if __name__ == '__main__':
    unittest.main()
