
import pytest
from unittest.mock import MagicMock
from simulation.metrics.economic_tracker import EconomicIndicatorTracker
from modules.analytics.api import EconomyAnalyticsSnapshotDTO, HouseholdAnalyticsDTO, FirmAnalyticsDTO, MarketAnalyticsDTO

from simulation.models import Transaction
from simulation.markets.order_book_market import OrderBookMarket

def test_indicator_aggregation(simple_household, mock_config_registry):
    """Spec 2: EconomicIndicatorTracker 지표 집계 검증"""
    # Arrange
    # Initialize Tracker with config
    tracker = EconomicIndicatorTracker(config_module=mock_config_registry)

    # Setup Household state
    # tracker calculates total_consumption from household._econ_state.consumption_expenditure_this_tick_pennies
    simple_household._econ_state.consumption_expenditure_this_tick_pennies = 1000
    simple_household.is_active = True

    # Act
    # Create DTO
    h_dto = HouseholdAnalyticsDTO(
        agent_id=1,
        is_active=True,
        total_cash_pennies=0,
        portfolio_value_pennies=0,
        is_employed=False,
        trust_score=0.5,
        survival_need=0.5,
        consumption_expenditure_pennies=1000,
        food_expenditure_pennies=0,
        labor_income_pennies=0,
        education_level=1.0,
        aptitude=0.5
    )

    snapshot = EconomyAnalyticsSnapshotDTO(
        tick=1,
        households=[h_dto],
        firms=[],
        markets=[],
        money_supply_pennies=0,
        m2_leak_pennies=0,
        monetary_base_pennies=0
    )

    tracker.track_tick(snapshot)

    # Assert
    # Check self.metrics for "total_consumption"
    latest_metrics = tracker.get_latest_indicators()

    print(f"Latest metrics: {latest_metrics}")

    assert "total_consumption" in latest_metrics
    assert latest_metrics["total_consumption"] == 1000 # 1000 pennies (int)
