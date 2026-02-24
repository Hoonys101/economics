import pytest
from unittest.mock import MagicMock
from modules.government.engines.fiscal_engine import FiscalEngine
from modules.government.engines.api import FiscalStateDTO, FiscalRequestDTO, FiscalDecisionDTO, FiscalConfigDTO
from modules.system.api import MarketSnapshotDTO

def test_fiscal_engine_decide_structure():
    config = FiscalConfigDTO(
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
    engine = FiscalEngine(config)

    state = FiscalStateDTO(
        tick=100,
        assets={"USD": 1000}, # Corrected to int
        total_debt=500.0,
        income_tax_rate=0.1,
        corporate_tax_rate=0.2,
        approval_rating=0.5,
        welfare_budget_multiplier=1.0,
        potential_gdp=10000.0
    )

    market = MarketSnapshotDTO(
        tick=100,
        market_signals={},
        market_data={"current_gdp": 10000.0}
    )

    decision = engine.decide(state, market, [])

    assert isinstance(decision, FiscalDecisionDTO)
    assert decision.new_income_tax_rate is not None
    assert decision.new_corporate_tax_rate is not None
