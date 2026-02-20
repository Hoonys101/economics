import pytest
from unittest.mock import MagicMock
from modules.government.engines.fiscal_engine import FiscalEngine
from modules.government.engines.api import FiscalStateDTO, FiscalRequestDTO, FirmBailoutRequestDTO, FirmFinancialsDTO, FiscalDecisionDTO
from modules.system.api import MarketSnapshotDTO
from modules.system.api import DEFAULT_CURRENCY

@pytest.fixture
def mock_config():
    config = MagicMock()
    config.AUTO_COUNTER_CYCLICAL_ENABLED = True
    config.FISCAL_SENSITIVITY_ALPHA = 0.5
    config.INCOME_TAX_RATE = 0.1
    config.CORPORATE_TAX_RATE = 0.2
    config.TICKS_PER_YEAR = 100
    config.BAILOUT_INTEREST_RATE = 0.05
    config.BAILOUT_TERM_TICKS = 365
    return config

@pytest.fixture
def fiscal_engine(mock_config):
    return FiscalEngine(mock_config)

class TestFiscalEngine:
    def test_decide_expansionary(self, fiscal_engine):
        # Case: GDP < Potential (Recession) -> Should lower tax
        state = FiscalStateDTO(
            tick=100,
            assets={DEFAULT_CURRENCY: 1000.0},
            total_debt=0.0,
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
                "inflation_rate_annual": 0.02,
                "current_gdp": 900.0 # Gap = (900-1000)/1000 = -0.1
            }
        )

        requests = []

        decision = fiscal_engine.decide(state, market, requests)

        # Stance = -0.5 * -0.1 = 0.05
        # New Tax = 0.1 * (1 - 0.05) = 0.095

        assert isinstance(decision, FiscalDecisionDTO)
        assert decision.new_income_tax_rate < 0.1
        assert decision.new_corporate_tax_rate < 0.2
        assert decision.new_income_tax_rate == pytest.approx(0.095)

    def test_decide_contractionary(self, fiscal_engine):
        # Case: GDP > Potential (Boom) -> Should raise tax
        state = FiscalStateDTO(
            tick=100,
            assets={DEFAULT_CURRENCY: 1000.0},
            total_debt=0.0,
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
                "inflation_rate_annual": 0.02,
                "current_gdp": 1100.0 # Gap = 0.1
            }
        )

        decision = fiscal_engine.decide(state, market, [])

        # Stance = -0.5 * 0.1 = -0.05
        # New Tax = 0.1 * (1 - (-0.05)) = 0.105

        assert isinstance(decision, FiscalDecisionDTO)
        assert decision.new_income_tax_rate > 0.1
        assert decision.new_income_tax_rate == pytest.approx(0.105)

    def test_evaluate_bailout_solvent(self, fiscal_engine):
        state = FiscalStateDTO(
            tick=100,
            assets={},
            total_debt=0.0,
            income_tax_rate=0.1,
            corporate_tax_rate=0.2,
            approval_rating=0.5,
            welfare_budget_multiplier=1.0,
            potential_gdp=1000.0
        )
        market = MarketSnapshotDTO(
            tick=100,
            market_signals={},
            market_data={"current_gdp": 1000.0, "inflation_rate_annual": 0.0}
        )

        req = FiscalRequestDTO(
            bailout_request=FirmBailoutRequestDTO(
                firm_id=101,
                requested_amount=500,
                firm_financials=FirmFinancialsDTO(
                    assets=1000,
                    profit=-100.0,
                    is_solvent=True
                )
            )
        )

        decision = fiscal_engine.decide(state, market, [req])

        assert isinstance(decision, FiscalDecisionDTO)
        assert len(decision.bailouts_to_grant) == 1
        grant = decision.bailouts_to_grant[0]
        assert grant.firm_id == 101
        assert grant.amount == 500.0

    def test_evaluate_bailout_insolvent(self, fiscal_engine):
        state = FiscalStateDTO(
            tick=100,
            assets={},
            total_debt=0.0,
            income_tax_rate=0.1,
            corporate_tax_rate=0.2,
            approval_rating=0.5,
            welfare_budget_multiplier=1.0,
            potential_gdp=1000.0
        )
        market = MarketSnapshotDTO(
            tick=100,
            market_signals={},
            market_data={"current_gdp": 1000.0, "inflation_rate_annual": 0.0}
        )

        req = FiscalRequestDTO(
            bailout_request=FirmBailoutRequestDTO(
                firm_id=102,
                requested_amount=500,
                firm_financials=FirmFinancialsDTO(
                    assets=0,
                    profit=-100.0,
                    is_solvent=False
                )
            )
        )

        decision = fiscal_engine.decide(state, market, [req])

        assert isinstance(decision, FiscalDecisionDTO)
        assert len(decision.bailouts_to_grant) == 0
