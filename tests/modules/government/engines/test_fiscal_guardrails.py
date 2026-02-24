import pytest
from unittest.mock import MagicMock
from modules.government.engines.fiscal_engine import FiscalEngine
from modules.government.engines.api import FiscalStateDTO, FiscalRequestDTO, FirmBailoutRequestDTO, FirmFinancialsDTO, FiscalConfigDTO
from modules.system.api import MarketSnapshotDTO, DEFAULT_CURRENCY

@pytest.fixture
def mock_config():
    return FiscalConfigDTO(
        tax_rate_min=0.05,
        tax_rate_max=0.60,
        base_income_tax_rate=0.1,
        base_corporate_tax_rate=0.2,
        debt_ceiling_ratio=1.5,
        austerity_trigger_ratio=1.0,
        fiscal_sensitivity_alpha=0.5,
        auto_counter_cyclical_enabled=True,
        tax_adjustment_step=0.01,
        debt_ceiling_hard_limit_ratio=1.5
    )

@pytest.fixture
def fiscal_engine(mock_config):
    return FiscalEngine(mock_config)

class TestFiscalGuardrails:

    def test_debt_brake_welfare_reduction(self, fiscal_engine):
        """Test that high debt reduces welfare multiplier."""
        # 1500 debt / 1000 GDP = 1.5 ratio -> Should trigger reduction
        state = FiscalStateDTO(
            tick=100,
            assets={DEFAULT_CURRENCY: 1000.0},
            total_debt=1500.0,
            income_tax_rate=0.1,
            corporate_tax_rate=0.2,
            approval_rating=0.5,
            welfare_budget_multiplier=1.0,
            potential_gdp=1000.0
        )

        market = MarketSnapshotDTO(
            tick=100,
            market_signals={},
            market_data={
                "current_gdp": 1000.0
            }
        )

        decision = fiscal_engine.decide(state, market, [])

        # Expect multiplier to be reduced below 1.0
        assert decision.new_welfare_budget_multiplier < 1.0

    def test_debt_brake_extreme_welfare_cut(self, fiscal_engine):
        """Test that extreme debt triggers severe welfare cuts."""
        # 2000 debt / 1000 GDP = 2.0 ratio -> Severe cut
        state = FiscalStateDTO(
            tick=100,
            assets={DEFAULT_CURRENCY: 1000.0},
            total_debt=2000.0,
            income_tax_rate=0.1,
            corporate_tax_rate=0.2,
            approval_rating=0.5,
            welfare_budget_multiplier=1.0,
            potential_gdp=1000.0
        )

        market = MarketSnapshotDTO(
            tick=100,
            market_signals={},
            market_data={"current_gdp": 1000.0}
        )

        decision = fiscal_engine.decide(state, market, [])

        assert decision.new_welfare_budget_multiplier <= 0.5

    def test_debt_brake_tax_hike_in_recession(self, fiscal_engine):
        """
        Test that Debt Brake overrides Counter-Cyclical policy.
        Normally, a recession (GDP < Potential) lowers taxes.
        But with High Debt, taxes should NOT decrease (or should increase).
        """
        # Recession: 900 vs 1000 potential (-10% gap) -> Normally cuts tax
        # But Debt: 1600 / 1000 = 1.6 ratio -> Debt Brake active
        state = FiscalStateDTO(
            tick=100,
            assets={DEFAULT_CURRENCY: 1000.0},
            total_debt=1600.0,
            income_tax_rate=0.1,
            corporate_tax_rate=0.2,
            approval_rating=0.5,
            welfare_budget_multiplier=1.0,
            potential_gdp=1000.0
        )

        market = MarketSnapshotDTO(
            tick=100,
            market_signals={},
            market_data={"current_gdp": 900.0}
        )

        decision = fiscal_engine.decide(state, market, [])

        # Should NOT lower taxes below baseline (0.1)
        # Ideally should raise them
        assert decision.new_income_tax_rate >= 0.1
        assert decision.new_corporate_tax_rate >= 0.2

    def test_bailout_rejection_due_to_debt(self, fiscal_engine):
        """Test that bailouts are rejected if debt is too high."""
        state = FiscalStateDTO(
            tick=100,
            assets={DEFAULT_CURRENCY: 10000.0},
            total_debt=2000.0, # High Debt (Ratio 2.0)
            income_tax_rate=0.1,
            corporate_tax_rate=0.2,
            approval_rating=0.5,
            welfare_budget_multiplier=1.0,
            potential_gdp=1000.0
        )

        req = FiscalRequestDTO(
            bailout_request=FirmBailoutRequestDTO(
                firm_id=101,
                requested_amount=500.0,
                firm_financials=FirmFinancialsDTO(
                    assets=1000.0,
                    profit=-100.0,
                    is_solvent=True
                )
            )
        )

        market = MarketSnapshotDTO(
            tick=100,
            market_signals={},
            market_data={"current_gdp": 1000.0}
        )

        decision = fiscal_engine.decide(state, market, [req])

        assert len(decision.bailouts_to_grant) == 0

    def test_bailout_rejection_due_to_insufficient_funds(self, fiscal_engine):
        """
        Test that bailouts are rejected if government is broke AND cannot borrow safely.
        If Debt/GDP > 1.0 (Austerity), we shouldn't borrow for bailouts.
        We must have cash on hand.
        """
        state = FiscalStateDTO(
            tick=100,
            assets={DEFAULT_CURRENCY: 100.0}, # Only 100 cash
            total_debt=1100.0, # Moderate Debt (Ratio 1.1) -> austerity trigger
            income_tax_rate=0.1,
            corporate_tax_rate=0.2,
            approval_rating=0.5,
            welfare_budget_multiplier=1.0,
            potential_gdp=1000.0
        )

        req = FiscalRequestDTO(
            bailout_request=FirmBailoutRequestDTO(
                firm_id=101,
                requested_amount=500.0,
                firm_financials=FirmFinancialsDTO(
                    assets=1000.0,
                    profit=-100.0,
                    is_solvent=True
                )
            )
        )

        market = MarketSnapshotDTO(
            tick=100,
            market_signals={},
            market_data={"current_gdp": 1000.0}
        )

        decision = fiscal_engine.decide(state, market, [req])

        assert len(decision.bailouts_to_grant) == 0
