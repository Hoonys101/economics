import unittest
from unittest.mock import Mock, MagicMock
from simulation.agents.government import Government
import config

class TestFiscalPolicy(unittest.TestCase):
    def setUp(self):
        # Configure Mock Config
        self.config = Mock()
        self.config.FISCAL_SENSITIVITY_ALPHA = 0.5
        self.config.POTENTIAL_GDP_WINDOW = 50
        self.config.TAX_RATE_MIN = 0.05
        self.config.TAX_RATE_MAX = 0.30
        self.config.TAX_RATE_BASE = 0.10
        self.config.DEBT_CEILING_RATIO = 1.0
        self.config.FISCAL_STANCE_EXPANSION_THRESHOLD = 0.025
        self.config.FISCAL_STANCE_CONTRACTION_THRESHOLD = -0.025

        # Government Instance
        self.gov = Government(id=1, initial_assets=1000.0, config_module=self.config)
        self.gov.effective_tax_rate = 0.10 # Explicit set for clarity

    def test_potential_gdp_ema_convergence(self):
        """Test that potential GDP converges using EMA."""
        # Initial GDP
        self.gov.adjust_fiscal_policy(current_gdp=1000.0)
        self.assertEqual(self.gov.potential_gdp, 1000.0)

        # Update with same GDP, should stay same
        self.gov.adjust_fiscal_policy(current_gdp=1000.0)
        self.assertAlmostEqual(self.gov.potential_gdp, 1000.0)

        # Update with higher GDP, should increase but lag
        self.gov.adjust_fiscal_policy(current_gdp=2000.0)
        # alpha = 2/(50+1) = 2/51 approx 0.039
        # new = 2000 * 0.039 + 1000 * (1-0.039) = 78 + 961 = 1039 approx
        self.assertTrue(1000.0 < self.gov.potential_gdp < 2000.0)

    def test_counter_cyclical_tax_adjustment_recession(self):
        """
        Test Fiscal Expansion during Recession (GDP < Potential).
        GDP Drops -> Output Gap Negative -> Fiscal Stance Positive -> Tax Rate Lowers
        """
        # Set stable potential GDP
        self.gov.potential_gdp = 1000.0

        # Sudden drop in current GDP (Recession)
        current_gdp = 800.0 # 20% drop
        self.gov.adjust_fiscal_policy(current_gdp)

        # Calculate expected values accounting for EMA update
        # Alpha for EMA = 2 / (50 + 1) = 2/51
        ema_alpha = 2 / 51
        expected_potential = current_gdp * ema_alpha + 1000.0 * (1 - ema_alpha)
        expected_gap = (current_gdp - expected_potential) / expected_potential
        expected_stance = -0.5 * expected_gap
        expected_tax = 0.1 * (1.0 - expected_stance)

        self.assertAlmostEqual(self.gov.fiscal_stance, expected_stance)
        self.assertAlmostEqual(self.gov.effective_tax_rate, expected_tax)
        self.assertLess(self.gov.effective_tax_rate, 0.10)

    def test_counter_cyclical_tax_adjustment_boom(self):
        """
        Test Fiscal Contraction during Boom (GDP > Potential).
        GDP Rises -> Output Gap Positive -> Fiscal Stance Negative -> Tax Rate Increases
        """
        # Set stable potential GDP
        self.gov.potential_gdp = 1000.0

        # Sudden rise in current GDP (Boom)
        current_gdp = 1200.0 # 20% rise
        self.gov.adjust_fiscal_policy(current_gdp)

        # Calculate expected values accounting for EMA update
        ema_alpha = 2 / 51
        expected_potential = current_gdp * ema_alpha + 1000.0 * (1 - ema_alpha)
        expected_gap = (current_gdp - expected_potential) / expected_potential
        expected_stance = -0.5 * expected_gap
        expected_tax = 0.1 * (1.0 - expected_stance)

        self.assertAlmostEqual(self.gov.fiscal_stance, expected_stance)
        self.assertAlmostEqual(self.gov.effective_tax_rate, expected_tax)
        self.assertGreater(self.gov.effective_tax_rate, 0.10)

    def test_debt_ceiling_enforcement(self):
        """Test that spending is blocked when Debt Ceiling is hit."""
        self.gov.assets = 0.0
        self.gov.total_debt = 0.0
        self.gov.potential_gdp = 1000.0

        agent = Mock()
        agent.assets = 0.0

        # 1. Spend within limit
        # Limit is 1.0 * 1000 = 1000
        amount = 500.0
        paid = self.gov.provide_subsidy(agent, amount, current_tick=1)
        self.assertEqual(paid, 500.0)
        self.assertEqual(self.gov.total_debt, 500.0)

        # 2. Spend to hit limit
        amount = 500.0
        paid = self.gov.provide_subsidy(agent, amount, current_tick=2)
        self.assertEqual(paid, 500.0)
        self.assertEqual(self.gov.total_debt, 1000.0)

        # 3. Try to spend ABOVE limit
        # Debt Ratio is now 1000/1000 = 1.0.
        # Logic says: if current_debt_ratio >= ceiling, block.
        # So next spend should fail if assets are 0.
        amount = 100.0
        paid = self.gov.provide_subsidy(agent, amount, current_tick=3)
        self.assertEqual(paid, 0.0)
        self.assertEqual(self.gov.total_debt, 1000.0) # Debt should not increase

    def test_calculate_income_tax_uses_effective_rate(self):
        """Verify income tax calculation uses the adaptive effective rate."""
        self.gov.effective_tax_rate = 0.05 # Lowered rate
        self.config.TAX_MODE = "FLAT"

        income = 100.0
        tax = self.gov.calculate_income_tax(income, survival_cost=10.0)
        self.assertEqual(tax, 5.0)

        # Test Progressive Mode scaling
        self.config.TAX_MODE = "PROGRESSIVE"
        self.config.TAX_BRACKETS = [(1000.0, 0.2)] # Simple flat bracket for testing
        # Base was 0.1, Effective is 0.05. Scaling factor = 0.5.
        # Raw tax = 100 * 0.2 = 20.
        # Adjusted tax = 20 * 0.5 = 10.

        tax = self.gov.calculate_income_tax(income, survival_cost=10.0)
        self.assertEqual(tax, 10.0)
