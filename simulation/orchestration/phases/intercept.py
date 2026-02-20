from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional
import logging

from simulation.orchestration.api import IPhaseStrategy
from simulation.dtos.api import SimulationState
from modules.system.services.command_service import CommandService
from simulation.dtos.commands import GodCommandDTO

if TYPE_CHECKING:
    from simulation.world_state import WorldState

logger = logging.getLogger(__name__)

class Phase0_Intercept(IPhaseStrategy):
    """
    FOUND-03: Phase 0 (Intercept) - The Sovereign Slot.
    Executes God-Mode commands before the simulation logic begins.
    Enforces strict causality and M2 integrity.
    """

    def __init__(self, world_state: WorldState):
        self.world_state = world_state
        self.command_service: Optional[CommandService] = None

    def _ensure_service_initialized(self):
        if self.command_service:
            return

        world_state = self.world_state
        # Validation (FOUND-03 requirement)
        if not hasattr(world_state, 'global_registry') or not world_state.global_registry:
             raise RuntimeError("GlobalRegistry not initialized in WorldState (FOUND-03 requirement).")
        if not world_state.settlement_system:
             raise RuntimeError("SettlementSystem not initialized in WorldState.")

        # AgentRegistry resolution
        agent_registry = None
        if hasattr(world_state.settlement_system, 'agent_registry'):
            agent_registry = world_state.settlement_system.agent_registry

        if not agent_registry:
             # Fallback attempt via sim attributes if available on world_state (unlikely but safe)
             if hasattr(world_state, 'agent_registry'):
                 agent_registry = getattr(world_state, 'agent_registry')
             else:
                 pass

        if not agent_registry:
             raise RuntimeError("AgentRegistry not found linked to SettlementSystem.")

        self.command_service = CommandService(
            registry=world_state.global_registry,
            settlement_system=world_state.settlement_system,
            agent_registry=agent_registry
        )

    def execute(self, state: SimulationState) -> SimulationState:
        self._ensure_service_initialized()

        # 1. Fetch pending God-Mode commands
        # Assumes TickOrchestrator drained WorldState.god_command_queue into state.god_command_snapshot
        pending_commands: List[GodCommandDTO] = state.god_command_snapshot

        if not pending_commands:
            return state

        logger.info(
            f"PHASE_0_INTERCEPT | Processing {len(pending_commands)} God-Mode commands.",
            extra={"tick": state.time, "count": len(pending_commands)}
        )

        # 2. Dispatch Commands via CommandService Protocol
        try:
            # CommandService handles Validation -> Snapshot -> Mutation -> Audit -> Commit/Rollback
            baseline_m2 = int(self.world_state.baseline_money_supply)
            results = self.command_service.execute_command_batch(pending_commands, state.time, baseline_m2)

            total_net_injection = 0
            all_success = True

            for res in results:
                if not res.success:
                    logger.warning(
                        f"PHASE_0_CMD_FAIL | ID: {res.command_id}, Reason: {res.failure_reason}, Rollback: {res.rollback_performed}"
                    )
                    all_success = False
                else:
                    logger.info(f"PHASE_0_CMD_SUCCESS | ID: {res.command_id}")
                    if res.audit_report and "m2_delta" in res.audit_report:
                        total_net_injection += res.audit_report["m2_delta"]

            # 3. Update Baseline if successful
            # Since CommandService is atomic, if any failed, the whole batch was rolled back (in our implementation).
            # If all success (or rather, if the batch was committed), we update the baseline.
            # Currently CommandService rolls back entire batch on failure.
            # So if results contain any success, they should ALL be success.
            # If results contain failure, they should ALL be failure (or rolled back).

            if all_success and total_net_injection != 0:
                 self.world_state.baseline_money_supply += total_net_injection
                 logger.info(
                     f"PHASE_0_UPDATE | Baseline Money Supply updated by {total_net_injection}. New Baseline: {self.world_state.baseline_money_supply}"
                 )

        except Exception as e:
            logger.critical(f"PHASE_0_FATAL | Dispatch failed: {e}", exc_info=True)
            # If unexpected exception occurs outside CommandService (unlikely), we rely on CommandService to have rolled back
            # or we might be in inconsistent state. But CommandService catches exceptions internally for the batch loop.
            pass

        # Clear commands to prevent re-execution
        state.god_command_snapshot.clear()

        return state
