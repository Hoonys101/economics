import pytest
from simulation.ai.altman_z_score import AltmanZScoreCalculator
from simulation.dtos.financial_dtos import FinancialStatementDTO

class TestAltmanZScoreCalculator:

    @pytest.fixture
    def calculator(self):
        return AltmanZScoreCalculator()

    def test_calculate_healthy_firm(self, calculator):
        """Test calculation for a healthy firm."""
        # Assets 1000, Working Capital 400, Retained Earnings 200, Avg Profit 100
        # X1 = 400/1000 = 0.4
        # X2 = 200/1000 = 0.2
        # X3 = 100/1000 = 0.1
        # Z = 1.2*0.4 + 1.4*0.2 + 3.3*0.1 = 0.48 + 0.28 + 0.33 = 1.09
        statement = FinancialStatementDTO(
            total_assets=1000.0,
            working_capital=400.0,
            retained_earnings=200.0,
            average_profit=100.0,
            total_debt=600.0
        )
        z_score = calculator.calculate(statement)
        assert z_score == pytest.approx(1.09, 0.001)

    def test_calculate_distressed_firm(self, calculator):
        """Test calculation for a distressed firm."""
        # Assets 1000, Working Capital -100, Retained Earnings -500, Avg Profit -50
        # X1 = -100/1000 = -0.1
        # X2 = -500/1000 = -0.5
        # X3 = -50/1000 = -0.05
        # Z = 1.2*-0.1 + 1.4*-0.5 + 3.3*-0.05 = -0.12 + -0.7 + -0.165 = -0.985
        statement = FinancialStatementDTO(
            total_assets=1000.0,
            working_capital=-100.0,
            retained_earnings=-500.0,
            average_profit=-50.0,
            total_debt=1100.0
        )
        z_score = calculator.calculate(statement)
        assert z_score == pytest.approx(-0.985, 0.001)

    def test_calculate_zero_assets(self, calculator):
        """Test calculation with zero total assets (should avoid division by zero)."""
        statement = FinancialStatementDTO(
            total_assets=0.0,
            working_capital=0.0,
            retained_earnings=0.0,
            average_profit=0.0,
            total_debt=0.0
        )
        z_score = calculator.calculate(statement)
        assert z_score == 0.0

    def test_calculate_high_solvency(self, calculator):
        """Test calculation for a highly solvent firm."""
        # High liquid assets, high retained earnings, high profit
        statement = FinancialStatementDTO(
            total_assets=1000.0,
            working_capital=800.0, # X1 = 0.8
            retained_earnings=500.0, # X2 = 0.5
            average_profit=300.0, # X3 = 0.3
            total_debt=200.0
        )
        # Z = 1.2*0.8 + 1.4*0.5 + 3.3*0.3 = 0.96 + 0.7 + 0.99 = 2.65
        z_score = calculator.calculate(statement)
        assert z_score == pytest.approx(2.65, 0.001)
