from __future__ import annotations
from typing import List, Dict, Any, Optional
from unittest.mock import MagicMock
from dataclasses import fields

from simulation.dtos.api import SimulationState, SystemCommand, GodCommandDTO
from modules.simulation.api import AgentID

class SimulationStateBuilder:
    """
    Builder for creating strict SimulationState instances for testing.
    Enforces DTO compliance and prevents Mock Drift.
    """

    def __init__(self):
        self._state_data: Dict[str, Any] = {
            "time": 0,
            "households": [],
            "firms": [],
            "agents": {},
            "markets": {},
            "primary_government": MagicMock(),
            "governments": [],
            "bank": MagicMock(),
            "central_bank": MagicMock(),
            "escrow_agent": None,
            "stock_market": None,
            "stock_tracker": None,
            "goods_data": {},
            "market_data": {},
            "config_module": MagicMock(),
            "tracker": MagicMock(),
            "logger": MagicMock(),
            "ai_training_manager": None,
            "ai_trainer": None,
            "settlement_system": MagicMock(),
            "next_agent_id": 100,
            "real_estate_units": [],
            "transactions": [],
            "inter_tick_queue": [],
            "effects_queue": [],
            "inactive_agents": {},
            "taxation_system": None,
            "currency_holders": [],
            "stress_scenario_config": None,
            "transaction_processor": None,
            "shareholder_registry": None,
            "housing_service": None,
            "registry": None,
            "saga_orchestrator": None,
            "monetary_ledger": None,
            "system_commands": [],
            "god_command_snapshot": [],
            "firm_pre_states": {},
            "household_pre_states": {},
            "household_time_allocation": {},
            "planned_consumption": {},
            "household_leisure_effects": {},
            "injectable_sensory_dto": None,
            "currency_registry_handler": None,
        }

    def with_time(self, tick: int) -> 'SimulationStateBuilder':
        self._state_data["time"] = tick
        return self

    def with_agent(self, agent_id: AgentID, agent: Any) -> 'SimulationStateBuilder':
        if "agents" not in self._state_data:
            self._state_data["agents"] = {}
        self._state_data["agents"][agent_id] = agent
        return self

    def with_system_command(self, command: SystemCommand) -> 'SimulationStateBuilder':
        if "system_commands" not in self._state_data:
            self._state_data["system_commands"] = []
        self._state_data["system_commands"].append(command)
        return self

    def with_god_command(self, command: GodCommandDTO) -> 'SimulationStateBuilder':
        if "god_command_snapshot" not in self._state_data:
            self._state_data["god_command_snapshot"] = []
        self._state_data["god_command_snapshot"].append(command)
        return self

    def with_primary_government(self, government: Any) -> 'SimulationStateBuilder':
        self._state_data["primary_government"] = government
        # Automatically sync with governments list to ensure consistency
        self._state_data["governments"] = [government]
        return self

    def build(self) -> SimulationState:
        """
        Builds the SimulationState instance.
        """
        # Validate against SimulationState fields to ensure no missing required fields
        # This acts as a compile-time check for tests if SimulationState changes
        try:
            return SimulationState(**self._state_data)
        except TypeError as e:
            # Check for missing arguments
            missing_args = []
            sim_fields = {f.name for f in fields(SimulationState)}
            provided_fields = set(self._state_data.keys())
            missing_fields = sim_fields - provided_fields
            if missing_fields:
                raise ValueError(f"SimulationStateBuilder is missing required fields: {missing_fields}") from e
            raise e
