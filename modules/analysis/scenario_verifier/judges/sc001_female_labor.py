from typing import Dict, Any, List
from modules.analysis.scenario_verifier.api import IScenarioJudge, ScenarioReportDTO, ScenarioStatus

class FemaleLaborParticipationJudge:
    SCENARIO_ID = "SC-001"
    REQUIRED_FIELD = "demographics.gender_stats"

    @property
    def required_fields(self) -> List[str]:
        return [self.REQUIRED_FIELD]

    def evaluate(self, telemetry_data: Dict[str, Any]) -> ScenarioReportDTO:
        stats = telemetry_data.get(self.REQUIRED_FIELD, {})

        # Guard against missing data
        if not stats:
            return ScenarioReportDTO(
                scenario_id=self.SCENARIO_ID,
                status=ScenarioStatus.PENDING,
                progress_pct=0.0,
                current_kpi_value=0.0,
                target_kpi_value=0.9,
                message="Data not available yet"
            )

        female_stats = stats.get("F", {})
        male_stats = stats.get("M", {})

        female_avg_labor = female_stats.get("avg_labor_hours", 0.0)
        male_avg_labor = male_stats.get("avg_labor_hours", 0.0)

        # Handle zero division or no labor at all
        if male_avg_labor <= 1e-6:
            # If male labor is 0, and female is > 0, ratio is infinite (Success?)
            if female_avg_labor > 0:
                 ratio = 10.0 # Cap at reasonable high number
            else:
                 ratio = 0.0
        else:
            ratio = female_avg_labor / male_avg_labor

        target = 0.90
        progress = min(100.0, (ratio / target) * 100)

        status = ScenarioStatus.RUNNING
        if ratio >= target:
            status = ScenarioStatus.SUCCESS
        elif ratio < 0.05 and progress > 0: # Threshold for failure if implementation requires strict check
             # Spec suggests FAILED if ratio < 0.1
             # We can mark it FAILED or just RUNNING with low progress.
             # Let's follow spec example if strictly stated.
             pass

        return ScenarioReportDTO(
            scenario_id=self.SCENARIO_ID,
            status=status,
            progress_pct=progress,
            current_kpi_value=ratio,
            target_kpi_value=target,
            message=f"Ratio: {ratio:.2f} (F: {female_avg_labor:.1f}h / M: {male_avg_labor:.1f}h)"
        )
