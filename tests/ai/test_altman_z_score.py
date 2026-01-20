import pytest
from simulation.ai.altman_z_score import AltmanZScoreCalculator
from simulation.dtos.financial_dtos import FinancialStatementDTO

class TestAltmanZScoreCalculator:

    @pytest.fixture
    def calculator(self):
        return AltmanZScoreCalculator()

    def test_calculate_healthy_firm(self, calculator):
        # High assets, low debt, good profit
        dto = FinancialStatementDTO(
            total_assets=1000.0,
            working_capital=500.0,   # 0.5 * 1.2 = 0.6
            retained_earnings=300.0, # 0.3 * 1.4 = 0.42
            average_profit=200.0,    # 0.2 * 3.3 = 0.66
            total_debt=100.0
        )
        # Expected: 0.6 + 0.42 + 0.66 = 1.68
        # Wait, let's calculate exactly
        # X1 = 500/1000 = 0.5; * 1.2 = 0.6
        # X2 = 300/1000 = 0.3; * 1.4 = 0.42
        # X3 = 200/1000 = 0.2; * 3.3 = 0.66
        # Total = 1.68

        score = calculator.calculate(dto)
        assert score == pytest.approx(1.68)

    def test_calculate_distressed_firm(self, calculator):
        # Low working capital, losses
        dto = FinancialStatementDTO(
            total_assets=1000.0,
            working_capital=50.0,    # 0.05 * 1.2 = 0.06
            retained_earnings=-100.0,# -0.1 * 1.4 = -0.14
            average_profit=-50.0,    # -0.05 * 3.3 = -0.165
            total_debt=800.0
        )
        # Expected: 0.06 - 0.14 - 0.165 = -0.245

        score = calculator.calculate(dto)
        assert score == pytest.approx(-0.245)

    def test_calculate_zero_assets(self, calculator):
        dto = FinancialStatementDTO(
            total_assets=0.0,
            working_capital=0.0,
            retained_earnings=0.0,
            average_profit=0.0,
            total_debt=0.0
        )
        score = calculator.calculate(dto)
        assert score == 0.0
