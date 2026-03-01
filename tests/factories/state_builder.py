from simulation.dtos.api import SimulationState
from simulation.dtos.api import CommandBatchDTO
from typing import Any, Dict
from unittest.mock import MagicMock

class SimulationStateBuilder:
    def __init__(self) -> None:
        self.state_kwargs: Dict[str, Any] = {
            "time": 0,
            "households": [],
            "firms": [],
            "agents": {},
            "markets": {},
            "primary_government": None,
            "bank": None,
            "central_bank": None,
            "goods_data": {},
            "market_data": {},
            "config_module": None,
            "tracker": None,
            "logger": None,
            "command_batch": CommandBatchDTO(tick=0),
            "god_commands": [],
            "system_commands": [],
            "real_estate_units": [],
            "escrow_agent": None,
            "stock_market": None,
            "stock_tracker": None,
            "ai_training_manager": None,
            "ai_trainer": None,
            "transactions": [],
            "inactive_agents": {}
        }

    def with_time(self, time: int) -> 'SimulationStateBuilder':
        self.state_kwargs["time"] = time
        return self

    def with_config(self, config: Any) -> 'SimulationStateBuilder':
        self.state_kwargs["config_module"] = config
        return self

    def build(self) -> SimulationState:
        if self.state_kwargs["config_module"] is None:
            self.state_kwargs["config_module"] = MagicMock()
        return SimulationState(**self.state_kwargs)
