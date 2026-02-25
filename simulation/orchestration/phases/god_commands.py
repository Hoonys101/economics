from __future__ import annotations
from typing import TYPE_CHECKING
import logging

from simulation.orchestration.api import IPhaseStrategy
from simulation.dtos.api import SimulationState

if TYPE_CHECKING:
    from simulation.world_state import WorldState
    from modules.system.services.command_service import CommandService

logger = logging.getLogger(__name__)

class Phase_GodCommands(IPhaseStrategy):
    """
    Executes God-Mode commands (System Control) from the unified command pipeline.
    """
    def __init__(self, world_state: 'WorldState', command_service: 'CommandService'):
        self.world_state = world_state
        self.command_service = command_service

    def execute(self, state: SimulationState) -> SimulationState:
        if not state.command_batch or not state.command_batch.god_commands:
            return state

        commands = state.command_batch.god_commands
        tick = state.time

        # Use baseline from WorldState as it is the persistent source
        baseline_m2 = getattr(self.world_state, "baseline_money_supply", 0)

        logger.info(f"GOD_COMMANDS_PHASE | Executing {len(commands)} commands.")

        results = self.command_service.execute_command_batch(commands, tick, baseline_m2)

        # Log results and Update Baseline (if injection happened)
        total_net_injection = 0
        all_success = True

        for result in results:
            if not result.success:
                logger.error(f"Command {result.command_id} failed: {result.failure_reason}")
                all_success = False
            else:
                logger.info(f"Command {result.command_id} succeeded.")
                if result.audit_report and "m2_delta" in result.audit_report:
                     total_net_injection += result.audit_report["m2_delta"]

        if all_success and total_net_injection != 0:
             # Update Baseline in WorldState
             self.world_state.baseline_money_supply += total_net_injection
             logger.info(
                 f"Baseline Money Supply updated by {total_net_injection}. New Baseline: {self.world_state.baseline_money_supply}"
             )

        return state
