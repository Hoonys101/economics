from modules.scenarios.api import Category as Category, IScenarioLoader as IScenarioLoader, ScenarioStrategy as ScenarioStrategy
from pathlib import Path
from typing import Any

class JsonScenarioLoader(IScenarioLoader):
    def load_strategy(self, source_id: str, raw_data: dict[str, Any]) -> ScenarioStrategy: ...
    def load_from_file(self, filepath: Path) -> ScenarioStrategy: ...
