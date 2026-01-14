import unittest
from unittest.mock import Mock, MagicMock
from simulation.systems.tax_agency import TaxAgency

class TestTaxAgency(unittest.TestCase):

    def setUp(self):
        self.mock_config = Mock()
        self.mock_config.TAX_BRACKETS = [
            (1.0, 0.10),
            (3.0, 0.20),
            (float('inf'), 0.30)
        ]
        self.mock_config.TAX_RATE_BASE = 0.20
        self.tax_agency = TaxAgency(self.mock_config)

    def test_calculate_income_tax_flat(self):
        self.assertAlmostEqual(self.tax_agency.calculate_income_tax(1000, 200, 0.25, 'FLAT'), 250)

    def test_calculate_income_tax_progressive_with_brackets(self):
        survival_cost = 1000
        current_tax_rate = 0.20 # Policy rate

        income = 2500
        tax_bracket1 = 1000 * 0.10
        tax_bracket2 = (2500 - 1000) * 0.20
        raw_tax = tax_bracket1 + tax_bracket2

        # With policy rate = base rate, adjustment_factor = 1.0
        expected_tax = raw_tax * (current_tax_rate / self.mock_config.TAX_RATE_BASE)

        self.assertAlmostEqual(self.tax_agency.calculate_income_tax(income, survival_cost, current_tax_rate, 'PROGRESSIVE'), expected_tax)

    def test_calculate_income_tax_progressive_scaling(self):
        survival_cost = 1000
        income = 2500
        raw_tax = (1000 * 0.10) + (1500 * 0.20) # 400

        # Policy rate is a tax cut (0.10) vs base (0.20), so factor is 0.5
        cut_rate = 0.10
        expected_tax_cut = raw_tax * (cut_rate / self.mock_config.TAX_RATE_BASE)
        self.assertAlmostEqual(self.tax_agency.calculate_income_tax(income, survival_cost, cut_rate, 'PROGRESSIVE'), expected_tax_cut)

        # Policy rate is a tax hike (0.30) vs base (0.20), so factor is 1.5
        hike_rate = 0.30
        expected_tax_hike = raw_tax * (hike_rate / self.mock_config.TAX_RATE_BASE)
        self.assertAlmostEqual(self.tax_agency.calculate_income_tax(income, survival_cost, hike_rate, 'PROGRESSIVE'), expected_tax_hike)

    def test_calculate_corporate_tax(self):
        self.assertAlmostEqual(self.tax_agency.calculate_corporate_tax(1000, 0.35), 350)
        self.assertAlmostEqual(self.tax_agency.calculate_corporate_tax(0, 0.35), 0)
        self.assertAlmostEqual(self.tax_agency.calculate_corporate_tax(-500, 0.35), 0)

    def test_collect_tax(self):
        mock_gov = MagicMock()
        mock_gov.assets = 10000
        mock_gov.total_collected_tax = 0
        # ... other attributes ...

        self.tax_agency.collect_tax(mock_gov, 100, "income", 1, 1)
        self.assertEqual(mock_gov.assets, 10100)

if __name__ == '__main__':
    unittest.main()
