import pytest
from unittest.mock import MagicMock
from modules.finance.engines.monetary_engine import MonetaryEngine
from modules.finance.engines.api import MonetaryStateDTO, MonetaryDecisionDTO
from modules.system.api import MarketSnapshotDTO

def test_monetary_engine_calculate_rate_structure():
    mock_config = MagicMock()
    mock_config.CB_TAYLOR_ALPHA = 1.5
    mock_config.CB_TAYLOR_BETA = 0.5
    engine = MonetaryEngine(config_module=mock_config)

    state = MonetaryStateDTO(
        tick=100,
        current_base_rate=0.05,
        potential_gdp=10000.0,
        inflation_target=0.02
    )

    market = MarketSnapshotDTO(
        tick=100,
        market_signals={},
        market_data={"current_gdp": 10000.0, "inflation_rate_annual": 0.03}
    )

    decision = engine.calculate_rate(state, market)

    assert isinstance(decision, MonetaryDecisionDTO)
    assert isinstance(decision.new_base_rate, float)
