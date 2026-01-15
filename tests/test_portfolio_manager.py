import unittest
from simulation.decisions.portfolio_manager import PortfolioManager
from simulation.dtos import MacroFinancialContext

class TestPortfolioManager(unittest.TestCase):

    def test_calculate_effective_risk_aversion_normal(self):
        """Test with normal economic conditions."""
        context = MacroFinancialContext(
            inflation_rate=0.02,
            gdp_growth_rate=0.03,
            market_volatility=0.1,
            interest_rate_trend=0.0
        )
        base_lambda = 1.0
        effective_lambda = PortfolioManager.calculate_effective_risk_aversion(base_lambda, context)
        self.assertAlmostEqual(effective_lambda, 1.0)

    def test_calculate_effective_risk_aversion_stagflation(self):
        """Test with stagflation."""
        context = MacroFinancialContext(
            inflation_rate=0.10,
            gdp_growth_rate=-0.02,
            market_volatility=0.3,
            interest_rate_trend=0.01
        )
        base_lambda = 1.0
        effective_lambda = PortfolioManager.calculate_effective_risk_aversion(base_lambda, context)
        self.assertAlmostEqual(effective_lambda, 1.92)

    def test_calculate_effective_risk_aversion_high_inflation(self):
        """Test with high inflation."""
        context = MacroFinancialContext(
            inflation_rate=0.20,
            gdp_growth_rate=0.01,
            market_volatility=0.2,
            interest_rate_trend=0.0
        )
        base_lambda = 1.0
        effective_lambda = PortfolioManager.calculate_effective_risk_aversion(base_lambda, context)
        self.assertAlmostEqual(effective_lambda, 2.8)

    def test_calculate_effective_risk_aversion_recession(self):
        """Test with a deep recession."""
        context = MacroFinancialContext(
            inflation_rate=0.01,
            gdp_growth_rate=-0.05,
            market_volatility=0.4,
            interest_rate_trend=0.0
        )
        base_lambda = 1.0
        effective_lambda = PortfolioManager.calculate_effective_risk_aversion(base_lambda, context)
        self.assertAlmostEqual(effective_lambda, 1.25)

    def test_calculate_effective_risk_aversion_cap(self):
        """Test the cap on the stress multiplier."""
        context = MacroFinancialContext(
            inflation_rate=0.50,
            gdp_growth_rate=-0.1,
            market_volatility=0.5,
            interest_rate_trend=0.0
        )
        base_lambda = 1.0
        effective_lambda = PortfolioManager.calculate_effective_risk_aversion(base_lambda, context)
        self.assertAlmostEqual(effective_lambda, 3.0)

if __name__ == '__main__':
    unittest.main()
