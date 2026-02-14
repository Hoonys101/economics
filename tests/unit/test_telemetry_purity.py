import pytest
from modules.system.server_bridge import TelemetryExchange
from simulation.dtos.telemetry import TelemetrySnapshotDTO
from modules.system.api import MarketSnapshotDTO

def test_telemetry_exchange_accepts_valid_dtos():
    te = TelemetryExchange()

    # Test TelemetrySnapshotDTO
    valid_telemetry = TelemetrySnapshotDTO(
        timestamp=100.0,
        tick=10,
        data={"key": "value"},
        errors=[],
        metadata={}
    )
    te.update(valid_telemetry)
    assert te.get() == valid_telemetry

    # Test MarketSnapshotDTO
    valid_market = MarketSnapshotDTO(
        tick=10,
        market_signals={},
        market_data={},
        housing=None,
        loan=None,
        labor=None
    )
    te.update(valid_market)
    assert te.get() == valid_market

def test_telemetry_exchange_rejects_invalid_types():
    te = TelemetryExchange()

    # Dict should be rejected
    with pytest.raises(TypeError, match="Invalid telemetry data type"):
        te.update({"tick": 10, "data": "bad"})

    # Int should be rejected
    with pytest.raises(TypeError):
        te.update(123)

    # None should be rejected based on my implementation
    with pytest.raises(TypeError):
        te.update(None)
