import unittest
from unittest.mock import MagicMock, PropertyMock
import pytest
from flask import Flask
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
    FinanceTabDataDTO
)
from simulation.core_agents import Household
from simulation.agents.government import Government
from simulation.metrics.economic_tracker import EconomicIndicatorTracker
from simulation.metrics.inequality_tracker import InequalityTracker
from simulation.markets.stock_market import StockMarket

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

        # Mock households
        h1 = MagicMock(spec=Household)
        h1.is_active = True
        h1.is_employed = True
        h1.needs = {"survival": 20.0}

        h2 = MagicMock(spec=Household)
        h2.is_active = True
        h2.is_employed = False
        h2.needs = {"survival": 60.0} # Struggling

        self.mock_simulation.households = [h1, h2]

        f1 = MagicMock()
        f1.is_active = True
        f1.total_shares = 1000.0
        f2 = MagicMock()
        f2.is_active = True
        f2.total_shares = 2000.0

        self.mock_simulation.firms = [f1, f2] # 2 firms
        self.mock_simulation.markets = {} # Empty markets for now

        self.vm = SnapshotViewModel(self.mock_repo)

    def test_get_dashboard_snapshot_structure(self):
        # Arrange
        current_tick = 100

        # Mock Global Indicators
        self.mock_tracker.get_latest_indicators.return_value = {
            "total_consumption": 50000.0,
            "avg_wage": 200.0,
            "unemployment_rate": 5.0
        }

        # Mock Inequality
        self.mock_inequality_tracker.calculate_wealth_distribution.return_value = {
            "gini_total_assets": 0.35
        }

        # Mock Attrition
        self.mock_repo.get_attrition_counts.return_value = {
            "bankruptcy_count": 2,
            "death_count": 5
        }

        # Mock Generation Stats
        self.mock_repo.get_generation_stats.return_value = [
            {"gen": 0, "count": 50, "avg_assets": 1000.0},
            {"gen": 1, "count": 50, "avg_assets": 500.0}
        ]

        # Mock Government
        self.mock_government.tax_revenue = {"income": 1000.0, "sales": 500.0}
        self.mock_government.total_collected_tax = 1500.0
        self.mock_government.total_spent_subsidies = 200.0
        self.mock_government.infrastructure_level = 1

        # Mock Market History
        self.mock_repo.get_economic_indicators.return_value = [
            {"avg_goods_price": 10.0, "avg_survival_need": 20.0},
            {"avg_goods_price": 11.0, "avg_survival_need": 21.0}
        ]

        # Mock Stock Market
        self.mock_stock_market.get_daily_volume.return_value = 1000.0
        self.mock_stock_market.get_stock_price.return_value = 10.0

        # Act
        snapshot = self.vm.get_dashboard_snapshot(self.mock_simulation, current_tick)

        # Assert
        assert isinstance(snapshot, DashboardSnapshotDTO)
        assert snapshot.tick == 100

        # Global Indicators
        assert snapshot.global_indicators.gdp == 50000.0
        assert snapshot.global_indicators.employment_rate == 95.0
        assert snapshot.global_indicators.gini == 0.35

        # Society Tab
        assert len(snapshot.tabs["society"].generations) == 2
        assert snapshot.tabs["society"].unemployment_pie["struggling"] == 1
        assert snapshot.tabs["society"].unemployment_pie["voluntary"] == 0

        # Government Tab
        assert snapshot.tabs["government"].tax_revenue["income"] == 1000.0
        assert snapshot.tabs["government"].fiscal_balance["revenue"] == 1500.0

        # Market Tab
        assert len(snapshot.tabs["market"].cpi) == 2
        assert len(snapshot.tabs["market"].maslow_fulfillment) == 2
        assert snapshot.tabs["market"].maslow_fulfillment[0] == 80.0 # 100 - 20

        # Finance Tab
        assert snapshot.tabs["finance"].volume == 1000.0

    def test_dashboard_api_endpoint_mock(self):
        # Verify DTO to Dict conversion (Contract check)
        from dataclasses import asdict

        # Act: Create a dummy DTO
        dto = DashboardSnapshotDTO(
            tick=100,
            global_indicators=DashboardGlobalIndicatorsDTO(
                death_rate=0.0, bankruptcy_rate=0.0, employment_rate=100.0,
                gdp=1000.0, avg_wage=10.0, gini=0.2
            ),
            tabs={
                "society": SocietyTabDataDTO(
                    generations=[], mitosis_cost=100.0, unemployment_pie={}
                ),
                "government": GovernmentTabDataDTO(
                    tax_revenue={}, fiscal_balance={}
                ),
                "market": MarketTabDataDTO(
                    commodity_volumes={}, cpi=[], maslow_fulfillment=[]
                ),
                "finance": FinanceTabDataDTO(
                    market_cap=1000.0, volume=100.0, turnover=0.1, dividend_yield=0.0
                )
            }
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
