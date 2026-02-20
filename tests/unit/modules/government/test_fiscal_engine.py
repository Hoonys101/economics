import pytest
from unittest.mock import MagicMock
from modules.government.engines.fiscal_engine import FiscalEngine
from modules.government.engines.api import FiscalStateDTO, FiscalRequestDTO, FiscalDecisionDTO
from modules.system.api import MarketSnapshotDTO

def test_fiscal_engine_decide_structure():
    engine = FiscalEngine()

    state = FiscalStateDTO(
        tick=100,
        assets={"USD": 1000.0},
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
