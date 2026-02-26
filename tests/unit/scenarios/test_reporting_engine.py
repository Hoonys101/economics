import pytest
from unittest.mock import MagicMock
from modules.scenarios.reporting_api import PhysicsIntegrityJudge, MacroHealthJudge, MicroSentimentJudge
from modules.system.api import IWorldStateMetricsProvider
from modules.simulation.dtos.api import MoneySupplyDTO
from modules.simulation.api import EconomicIndicatorsDTO
from modules.scenarios.api import Tier

class TestReportingEngine:

    @pytest.fixture
    def mock_world_state(self):
        mock = MagicMock(spec=IWorldStateMetricsProvider)
        return mock

    def test_physics_judge_metrics(self, mock_world_state):
        judge = PhysicsIntegrityJudge()
        assert judge.tier == Tier.PHYSICS
        assert judge.name == "PhysicsIntegrityJudge"

        # Setup mock return values
        mock_world_state.calculate_total_money.return_value = MoneySupplyDTO(
            total_m2_pennies=1000000,
            system_debt_pennies=50000,
            currency="USD"
        )

        metrics = judge.get_metrics(mock_world_state)

        assert metrics["m2_supply_pennies"] == 1000000
        assert metrics["system_debt_pennies"] == 50000
        assert metrics["m2_delta"] == 0 # Placeholder default

    def test_macro_judge_metrics(self, mock_world_state):
        judge = MacroHealthJudge()
        assert judge.tier == Tier.MACRO

        mock_world_state.get_economic_indicators.return_value = EconomicIndicatorsDTO(
            gdp=5000000.0,
            cpi=102.5,
            unemployment_rate=5.2
        )

        metrics = judge.get_metrics(mock_world_state)

        assert metrics["gdp"] == 5000000.0
        assert metrics["cpi"] == 102.5
        assert metrics["unemployment_rate"] == 5.2

    def test_micro_judge_metrics(self, mock_world_state):
        judge = MicroSentimentJudge()
        assert judge.tier == Tier.MICRO

        mock_world_state.get_market_panic_index.return_value = 0.95

        metrics = judge.get_metrics(mock_world_state)

        assert metrics["market_panic_index"] == 0.95
        assert metrics["withdrawal_pressure_alert"] is True # Threshold is 0.8

        mock_world_state.get_market_panic_index.return_value = 0.1
        metrics = judge.get_metrics(mock_world_state)
        assert metrics["withdrawal_pressure_alert"] is False

    def test_physics_judge_decision(self, mock_world_state):
        judge = PhysicsIntegrityJudge()
        # Currently stubbed to True
        assert judge.judge(mock_world_state) is True

    def test_macro_judge_decision(self, mock_world_state):
        judge = MacroHealthJudge()
        # Currently stubbed to True
        assert judge.judge(mock_world_state) is True

    def test_micro_judge_decision(self, mock_world_state):
        judge = MicroSentimentJudge()
        # Currently stubbed to True
        assert judge.judge(mock_world_state) is True
