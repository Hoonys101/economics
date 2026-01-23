import unittest
from unittest.mock import MagicMock, PropertyMock
import pytest
import json

from simulation.engine import Simulation
from simulation.db.repository import SimulationRepository
from simulation.viewmodels.snapshot_viewmodel import SnapshotViewModel
from simulation.dtos import (
    DashboardSnapshotDTO,
    DashboardGlobalIndicatorsDTO,
    SocietyTabDataDTO,
    GovernmentTabDataDTO,
    MarketTabDataDTO,
    FinanceTabDataDTO,
)
from simulation.core_agents import Household
from simulation.agents.government import Government
from simulation.metrics.economic_tracker import EconomicIndicatorTracker
from simulation.metrics.inequality_tracker import InequalityTracker
from simulation.markets.stock_market import StockMarket
from dataclasses import asdict


class TestDashboardAPI:
    def setup_method(self):
        self.mock_repo = MagicMock(spec=SimulationRepository)
        self.mock_simulation = MagicMock(spec=Simulation)
        self.mock_tracker = MagicMock(spec=EconomicIndicatorTracker)
        self.mock_inequality_tracker = MagicMock(spec=InequalityTracker)
        self.mock_government = MagicMock(spec=Government)
        self.mock_stock_market = MagicMock(spec=StockMarket)

        self.mock_simulation.tracker = self.mock_tracker
        self.mock_simulation.inequality_tracker = self.mock_inequality_tracker
        self.mock_simulation.government = self.mock_government
        self.mock_simulation.stock_market = self.mock_stock_market
        self.mock_simulation.run_id = 1
        self.mock_simulation.config_module = MagicMock()
        self.mock_simulation.config_module.TARGET_POPULATION = 100
        self.mock_simulation.config_module.MITOSIS_BASE_THRESHOLD = 1000.0
        self.mock_simulation.config_module.MITOSIS_SENSITIVITY = 1.0
        self.mock_simulation.config_module.INFRASTRUCTURE_INVESTMENT_COST = 5000.0
        self.mock_simulation.config_module.HOURS_PER_TICK = 24.0
        self.mock_simulation.config_module.SHOPPING_HOURS = 2.0

        # Patch missing attributes for Government mock
        self.mock_government.tax_history = []
        self.mock_government.welfare_history = []
        self.mock_government.education_history = []
        self.mock_government.current_tick_stats = {
            "education_spending": 0.0,
            "welfare_spending": 0.0,
            "stimulus_spending": 0.0,
            "total_collected": 0.0,
        }

        self.mock_simulation.markets = {}
        self.mock_simulation.household_time_allocation = {}

        self.vm = SnapshotViewModel(self.mock_repo)

    def test_get_dashboard_snapshot_structure(self, golden_households, golden_firms):
        # Arrange
        current_tick = 100

        # Inject Golden Fixtures
        # Patch households 'needs' and 'last_leisure_type' as done in generator
        for h in golden_households:
            if isinstance(h.needs, MagicMock):
                h.needs = {"survival": h.needs.survival}
            h.last_leisure_type = "IDLE"

        # Patch firms 'total_shares'
        for f in golden_firms:
            f.total_shares = 1000.0

        self.mock_simulation.households = golden_households
        self.mock_simulation.firms = golden_firms

        # Mock Global Indicators
        self.mock_tracker.get_latest_indicators.return_value = {
            "total_consumption": 50000.0,
            "avg_wage": 200.0,
            "unemployment_rate": 5.0,
        }

        # Mock Inequality
        self.mock_inequality_tracker.calculate_wealth_distribution.return_value = {
            "gini_total_assets": 0.35
        }

        # Mock Attrition
        self.mock_repo.get_attrition_counts.return_value = {
            "bankruptcy_count": 2,
            "death_count": 5,
        }

        # Mock Generation Stats
        self.mock_repo.get_generation_stats.return_value = [
            {"gen": 0, "count": 50, "avg_assets": 1000.0},
            {"gen": 1, "count": 50, "avg_assets": 500.0},
        ]

        # Mock Government
        self.mock_government.tax_revenue = {"income": 1000.0, "sales": 500.0}
        self.mock_government.total_collected_tax = 1500.0
        self.mock_government.total_spent_subsidies = 200.0
        self.mock_government.infrastructure_level = 1

        # Mock Market History
        self.mock_repo.get_economic_indicators.return_value = [
            {"avg_goods_price": 10.0, "avg_survival_need": 20.0},
            {"avg_goods_price": 11.0, "avg_survival_need": 21.0},
        ]

        # Mock Stock Market
        self.mock_stock_market.get_daily_volume.return_value = 1000.0
        self.mock_stock_market.get_stock_price.return_value = 10.0

        # Act
        snapshot = self.vm.get_dashboard_snapshot(self.mock_simulation, current_tick)

        # Assert against Golden Snapshot
        # Convert to dict
        result = asdict(snapshot)

        with open("tests/goldens/dashboard_snapshot.json") as f:
            expected = json.load(f)

        assert result == expected, "Dashboard structure changed"

    def test_dashboard_api_endpoint_mock(self):
        # Verify DTO to Dict conversion (Contract check)
        from dataclasses import asdict

        # Act: Create a dummy DTO
        dto = DashboardSnapshotDTO(
            tick=100,
            global_indicators=DashboardGlobalIndicatorsDTO(
                death_rate=0.0,
                bankruptcy_rate=0.0,
                employment_rate=100.0,
                gdp=1000.0,
                avg_wage=10.0,
                gini=0.2,
                avg_tax_rate=0.0,
                avg_leisure_hours=0.0,
                parenting_rate=0.0,
            ),
            tabs={
                "society": SocietyTabDataDTO(
                    generations=[],
                    mitosis_cost=100.0,
                    unemployment_pie={},
                    time_allocation={},
                    avg_leisure_hours=0.0,
                    avg_education_level=0.0,
                    brain_waste_count=0,
                ),
                "government": GovernmentTabDataDTO(
                    tax_revenue={},
                    fiscal_balance={},
                    tax_revenue_history=[],
                    welfare_spending=0.0,
                    current_avg_tax_rate=0.0,
                    welfare_history=[],
                    education_spending=0.0,
                    education_history=[],
                ),
                "market": MarketTabDataDTO(
                    commodity_volumes={}, cpi=[], maslow_fulfillment=[]
                ),
                "finance": FinanceTabDataDTO(
                    market_cap=1000.0, volume=100.0, turnover=0.1, dividend_yield=0.0
                ),
            },
        )

        # Verify it can be converted to dict (simulating what happens before jsonify)
        result = asdict(dto)

        assert result["tick"] == 100
        assert "global_indicators" in result
        assert result["global_indicators"]["gdp"] == 1000.0
        assert "tabs" in result
        assert "society" in result["tabs"]


if __name__ == "__main__":
    pytest.main([__file__])
