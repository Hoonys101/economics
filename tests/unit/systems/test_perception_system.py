import pytest
from unittest.mock import MagicMock
from collections import deque
from dataclasses import replace

from simulation.systems.perception_system import PerceptionSystem
from modules.system.api import MarketSnapshotDTO, MarketSignalDTO
from simulation.dtos.api import GovernmentPolicyDTO

@pytest.fixture
def mock_snapshot():
    return MarketSnapshotDTO(
        tick=10,
        market_signals={
            "food": MarketSignalDTO(
                market_id="food",
                item_id="food",
                best_bid=100,
                best_ask=110,
                last_traded_price=105,
                last_trade_tick=10,
                price_history_7d=[],
                volatility_7d=0.0,
                order_book_depth_buy=10,
                order_book_depth_sell=10,
                total_bid_quantity=100,
                total_ask_quantity=100,
                is_frozen=False
            )
        },
        market_data={
            "food_avg_price": 105.0
        },
        housing=None,
        loan=None,
        labor=None
    )

def test_perception_system_update(mock_snapshot):
    system = PerceptionSystem()
    system.update(mock_snapshot)
    assert system.current_snapshot == mock_snapshot
    assert len(system.snapshot_history) == 1

def test_smart_money_filter(mock_snapshot):
    system = PerceptionSystem()
    system.update(mock_snapshot)

    # Insight > 0.8
    filtered = system.apply_filter(0.9, mock_snapshot)
    assert filtered == mock_snapshot

def test_laggard_filter(mock_snapshot):
    system = PerceptionSystem()

    # Create history: Price 100, 110, 120
    prices = [100, 110, 120]
    for p in prices:
        snap = replace(mock_snapshot,
                       market_signals={"food": replace(mock_snapshot.market_signals["food"], last_traded_price=p)},
                       market_data={"food_avg_price": float(p)})
        system.update(snap)

    # Insight > 0.3 (MA 3)
    filtered = system.apply_filter(0.5, system.current_snapshot)

    # Expect avg of 100, 110, 120 -> 110
    expected_price = 110
    assert filtered.market_signals["food"].last_traded_price == expected_price
    assert filtered.market_data["food_avg_price"] == 110.0

def test_lemon_filter(mock_snapshot):
    system = PerceptionSystem()

    # Create history
    for i in range(10):
        snap = replace(mock_snapshot, tick=i)
        system.update(snap)

    # Insight <= 0.3 (Lag 5 + Noise)
    # Current tick is 9. Lag 5 means tick 4 (index -6)
    # History: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    # -1 is 9, -6 is 4.

    filtered = system.apply_filter(0.2, system.current_snapshot)

    # Base snapshot should be from tick 4
    assert filtered.tick == 4

def test_policy_filter():
    system = PerceptionSystem()
    policy = GovernmentPolicyDTO(
        income_tax_rate=0.1,
        sales_tax_rate=0.1,
        corporate_tax_rate=0.1,
        base_interest_rate=0.05,
        market_panic_index=0.5
    )

    # High Insight
    p1 = system.apply_policy_filter(0.9, policy)
    assert p1.market_panic_index == 0.5

    # Low Insight (0.0) -> Amplification 1.8x -> 0.9
    p2 = system.apply_policy_filter(0.0, policy)
    assert p2.market_panic_index == 0.9

    # Medium Insight (0.4) -> Amp 1.4x -> 0.7
    p3 = system.apply_policy_filter(0.4, policy)
    assert abs(p3.market_panic_index - 0.7) < 1e-9
