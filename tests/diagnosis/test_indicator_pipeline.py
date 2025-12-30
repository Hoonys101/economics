
import pytest
from unittest.mock import MagicMock
from simulation.metrics.economic_tracker import EconomicIndicatorTracker
from simulation.models import Transaction
from simulation.markets.order_book_market import OrderBookMarket

def test_indicator_aggregation(simple_household, mock_config_module):
    """Spec 2: EconomicIndicatorTracker 지표 집계 검증"""
    # Arrange
    # Initialize Tracker with config
    tracker = EconomicIndicatorTracker(config_module=mock_config_module)

    # Setup Household state
    # tracker calculates total_consumption from household.current_consumption
    simple_household.current_consumption = 10.0
    simple_household.is_active = True

    # Act
    # track(self, time: int, households: List[Household], firms: List[Firm], markets: Dict[str, Market])
    tracker.track(
        time=1,
        households=[simple_household],
        firms=[],
        markets={}
    )

    # Assert
    # Check self.metrics for "total_consumption"
    latest_metrics = tracker.get_latest_indicators()

    print(f"Latest metrics: {latest_metrics}")

    assert "total_consumption" in latest_metrics
    assert latest_metrics["total_consumption"] == 10.0
