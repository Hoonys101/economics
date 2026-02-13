import pytest
from unittest.mock import MagicMock
from modules.analysis.scenario_verifier.api import ScenarioStatus, ScenarioReportDTO
from modules.analysis.scenario_verifier.engine import ScenarioVerifier
from modules.analysis.scenario_verifier.judges.sc001_female_labor import FemaleLaborParticipationJudge

class TestScenarioVerifier:
    @pytest.fixture
    def mock_telemetry_collector(self):
        return MagicMock()

    @pytest.fixture
    def verifier(self):
        judge = FemaleLaborParticipationJudge()
        return ScenarioVerifier(judges=[judge])

    def test_initialize_subscribes_to_telemetry(self, verifier, mock_telemetry_collector):
        verifier.initialize(mock_telemetry_collector)
        mock_telemetry_collector.subscribe.assert_called_with(["demographics.gender_stats"], frequency_interval=1)

    def test_verify_tick_aggregates_reports(self, verifier):
        # Mock telemetry data: 18/20 = 0.9 (Target is 0.9)
        data = {
            "demographics.gender_stats": {
                "F": {"avg_labor_hours": 18.0},
                "M": {"avg_labor_hours": 20.0}
            }
        }

        reports = verifier.verify_tick(data)
        assert len(reports) == 1
        report = reports[0]
        assert report.scenario_id == "SC-001"
        assert report.status == ScenarioStatus.SUCCESS
        assert report.current_kpi_value == 0.9

    def test_verify_tick_handles_missing_data(self, verifier):
        data = {}
        reports = verifier.verify_tick(data)
        assert len(reports) == 1
        assert reports[0].status == ScenarioStatus.PENDING

    def test_verify_tick_handles_running_state(self, verifier):
        # Ratio 10/20 = 0.5 < 0.9 -> RUNNING
        data = {
            "demographics.gender_stats": {
                "F": {"avg_labor_hours": 10.0},
                "M": {"avg_labor_hours": 20.0}
            }
        }
        reports = verifier.verify_tick(data)
        assert len(reports) == 1
        assert reports[0].status == ScenarioStatus.RUNNING
        assert reports[0].current_kpi_value == 0.5

    def test_verify_tick_handles_exception_in_judge(self):
        judge = FemaleLaborParticipationJudge()
        # Mock evaluate to raise exception
        judge.evaluate = MagicMock(side_effect=RuntimeError("Test Error"))
        verifier = ScenarioVerifier(judges=[judge])

        reports = verifier.verify_tick({})
        assert len(reports) == 1
        assert reports[0].status == ScenarioStatus.FAILED
        assert "Test Error" in reports[0].message
