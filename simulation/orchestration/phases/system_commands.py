from __future__ import annotations
from typing import TYPE_CHECKING
import logging

from simulation.orchestration.api import IPhaseStrategy
from simulation.dtos.api import SimulationState
from modules.governance.processor import SystemCommandProcessor

if TYPE_CHECKING:
    from simulation.world_state import WorldState

logger = logging.getLogger(__name__)

class Phase_SystemCommands(IPhaseStrategy):
    """
    Orchestration phase for executing manual system commands (Cockpit interventions).
    This phase runs early in the tick to ensure interventions apply before agent decisions.
    """

    def __init__(self, world_state: 'WorldState'):
        self.world_state = world_state
        # Instantiate processor. Can be stateless or stateful.
        self.processor = SystemCommandProcessor()

    def execute(self, state: SimulationState) -> SimulationState:
        if not state.command_batch or not state.command_batch.system_commands:
            return state

        logger.info(
            f"SYSTEM_COMMANDS_PHASE | Processing {len(state.command_batch.system_commands)} commands.",
            extra={"tick": state.time, "count": len(state.command_batch.system_commands)}
        )

        for command in state.command_batch.system_commands:
            try:
                state = self.processor.execute(command, state)
            except Exception as e:
                logger.error(
                    f"SYSTEM_COMMAND_ERROR | Failed to execute command: {command}",
                    exc_info=True,
                    extra={"tick": state.time, "command": command}
                )

        # Commands are part of the tick batch, no need to clear as the batch is discarded next tick
        return state
