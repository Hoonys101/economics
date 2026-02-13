from __future__ import annotations
from typing import TYPE_CHECKING, List
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
                 raise RuntimeError("AgentRegistry not found linked to SettlementSystem.")

        self.command_service = CommandService(
            registry=world_state.global_registry,
            settlement_system=world_state.settlement_system,
            agent_registry=agent_registry
        )

    def execute(self, state: SimulationState) -> SimulationState:
        # 1. Fetch pending God-Mode commands
        # Assumes TickOrchestrator drained WorldState.god_command_queue into state.god_commands
        pending_commands: List[GodCommandDTO] = state.god_commands

        if not pending_commands:
            return state

        logger.info(
            f"PHASE_0_INTERCEPT | Processing {len(pending_commands)} God-Mode commands.",
            extra={"tick": state.time, "count": len(pending_commands)}
        )

        # 2. Dispatch Commands
        try:
            results = self.command_service.dispatch_commands(pending_commands)
            for res in results:
                logger.info(f"PHASE_0_RESULT | {res}")
        except Exception as e:
            logger.critical(f"PHASE_0_FATAL | Dispatch failed: {e}", exc_info=True)
            # Dispatch service should handle individual command errors, but if we crash here,
            # we should probably just return state to avoid crashing the whole sim if desired.
            # But "God Mode" implies power user, maybe better to crash?
            # Spec says "Engine should not crash."
            pass

        # 3. Audit Gate (M2 Integrity)
        # Calculate expected net injection from commands
        net_injection = 0
        for cmd in pending_commands:
            if cmd.command_type == "INJECT_MONEY" and cmd.amount:
                 net_injection += cmd.amount

        # Expected = Baseline (set at start of tick) + Net Injection
        expected_m2 = int(self.world_state.baseline_money_supply) + net_injection

        if not self.world_state.settlement_system.audit_total_m2(expected_total=expected_m2):
            logger.critical("PHASE_0_AUDIT_FAIL | M2 Integrity Compromised! Rolling back tick.")

            success = self.command_service.rollback_last_tick()
            if success:
                logger.info("PHASE_0_ROLLBACK | Successfully rolled back God-Mode intervention.")
                # No baseline update needed as we rolled back to original state
            else:
                 logger.critical("PHASE_0_ROLLBACK_FAIL | Rollback failed! State corrupted.")
                 raise RuntimeError("M2 Integrity Failure & Rollback Failed")
        else:
            # Audit Passed
            # Update baseline in WorldState to reflect valid injection so subsequent checks pass
            self.world_state.baseline_money_supply += net_injection
            logger.info(f"PHASE_0_SUCCESS | M2 Audit Passed. Baseline updated by {net_injection}.")

        # Clear commands to prevent re-execution
        state.god_commands.clear()

        return state
