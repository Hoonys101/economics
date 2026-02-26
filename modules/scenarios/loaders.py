import json
from pathlib import Path
from typing import Dict, Any
from modules.scenarios.api import IScenarioLoader, ScenarioStrategy, Category

class JsonScenarioLoader(IScenarioLoader):
    def load_strategy(self, source_id: str, raw_data: Dict[str, Any]) -> ScenarioStrategy:
        category_str = raw_data.get("category", "MONETARY")
        try:
            category = Category[category_str]
        except KeyError:
            category = Category.MONETARY

        return ScenarioStrategy(
            id=raw_data.get("id", source_id),
            category=category,
            config_params=raw_data.get("config_params", {}),
            duration_ticks=raw_data.get("duration_ticks", 100)
        )

    def load_from_file(self, filepath: Path) -> ScenarioStrategy:
        with open(filepath, 'r') as f:
            data = json.load(f)
        return self.load_strategy(filepath.stem, data)
