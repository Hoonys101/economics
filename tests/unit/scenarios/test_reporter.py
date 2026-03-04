import pytest
import os
from unittest.mock import MagicMock
from pathlib import Path
from modules.system.api import IWorldStateMetricsProvider
from modules.simulation.dtos.api import MoneySupplyDTO
from modules.simulation.api import EconomicIndicatorsDTO
from modules.scenarios.reporter import ScenarioReporter

class TestScenarioReporter:

    @pytest.fixture
    def mock_world_state(self):
        mock = MagicMock(spec=IWorldStateMetricsProvider)
        mock.calculate_total_money.return_value = MoneySupplyDTO(
            total_m2_pennies=1000000,
            system_debt_pennies=50000,
            currency="USD"
        )
        mock.get_economic_indicators.return_value = EconomicIndicatorsDTO(
            gdp=5000000.0,
            cpi=102.5,
            unemployment_rate=5.2
        )
        mock.get_market_panic_index.return_value = 0.95
        return mock

    def test_aggregate_reports(self, mock_world_state):
        reporter = ScenarioReporter()
        metrics = reporter.aggregate_reports(mock_world_state, "test_scenario_1")

        assert metrics["scenario_id"] == "test_scenario_1"

        # Check Physics
        assert metrics["physics"]["m2_supply_pennies"] == 1000000
        assert metrics["physics"]["system_debt_pennies"] == 50000

        # Check Macro
        assert metrics["macro"]["gdp"] == 5000000.0
        assert metrics["macro"]["cpi"] == 102.5
        assert metrics["macro"]["unemployment_rate"] == 5.2

        # Check Micro
        assert metrics["micro"]["market_panic_index"] == 0.95
        assert metrics["micro"]["withdrawal_pressure_alert"] is True

    def test_write_markdown_report(self, mock_world_state, tmp_path):
        reporter = ScenarioReporter()
        metrics = reporter.aggregate_reports(mock_world_state, "test_scenario_1")

        output_file = tmp_path / "test_report.md"
        reporter.write_markdown_report(metrics, "test_scenario_1", str(output_file))

        assert output_file.exists()

        content = output_file.read_text(encoding="utf-8")
        assert "## 📊 Scenario Evaluation Report: test_scenario_1" in content
        assert "* M2 Total: 1000000 pennies" in content
        assert "* System Debt: 50000 pennies" in content
        assert "* GDP Output: 5000000.0" in content
        assert "* CPI: 102.5" in content
        assert "* Panic Index: 0.95" in content
