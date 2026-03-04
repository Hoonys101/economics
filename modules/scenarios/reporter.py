from typing import Dict, Any
from pathlib import Path
from modules.system.api import IWorldStateMetricsProvider
from modules.scenarios.reporting_api import PhysicsIntegrityJudge, MacroHealthJudge, MicroSentimentJudge

class ScenarioReporter:
    """
    Orchestrator for 3-Tier Scenario Reporting.
    Aggregates metrics from Physics, Macro, and Micro judges and generates Markdown reports.
    """
    def __init__(self):
        self.physics_judge = PhysicsIntegrityJudge()
        self.macro_judge = MacroHealthJudge()
        self.micro_judge = MicroSentimentJudge()

    def aggregate_reports(self, world_state: IWorldStateMetricsProvider, scenario_id: str) -> Dict[str, Any]:
        """
        Harvests metrics from all three tiers and aggregates them into a single dictionary.
        """
        physics_metrics = self.physics_judge.get_metrics(world_state)
        macro_metrics = self.macro_judge.get_metrics(world_state)
        micro_metrics = self.micro_judge.get_metrics(world_state)

        return {
            "scenario_id": scenario_id,
            "physics": physics_metrics,
            "macro": macro_metrics,
            "micro": micro_metrics
        }

    def write_markdown_report(self, metrics_dict: Dict[str, Any], scenario_id: str, output_path: str) -> None:
        """
        Formats the aggregated metrics into a Markdown report and writes it to the specified path.
        """
        physics = metrics_dict.get("physics", {})
        macro = metrics_dict.get("macro", {})
        micro = metrics_dict.get("micro", {})

        report_content = f"""## 📊 Scenario Evaluation Report: {scenario_id}

### 🪐 Tier 1: Physics Integrity
* M2 Total: {physics.get('m2_supply_pennies', 0)} pennies
* System Debt: {physics.get('system_debt_pennies', 0)} pennies
* Zero-Sum Violation: {physics.get('m2_delta', 0)}

### 📈 Tier 2: Macro Health
* GDP Output: {macro.get('gdp', 0.0)}
* CPI: {macro.get('cpi', 0.0)}

### 👥 Tier 3: Micro Sentiment
* Panic Index: {micro.get('market_panic_index', 0.0)}
"""

        # Ensure the directory exists
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(report_content)
