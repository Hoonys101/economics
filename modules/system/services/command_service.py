from __future__ import annotations
from typing import List, Any, Optional, Protocol, Dict
from dataclasses import dataclass
import logging

from simulation.dtos.commands import GodCommandDTO
from modules.system.api import IGlobalRegistry, OriginType, IAgentRegistry
from modules.system.constants import ID_CENTRAL_BANK
from simulation.finance.api import ISettlementSystem, IFinancialAgent

logger = logging.getLogger(__name__)

class ICommandService(Protocol):
    def dispatch_commands(self, commands: List[GodCommandDTO]) -> List[str]:
        ...
    def rollback_last_tick(self) -> bool:
        ...
    def commit_last_tick(self) -> None:
        ...

@dataclass
class UndoRecord:
    command_type: str # "SET_PARAM" or "INJECT_MONEY"
    target_domain: Optional[str] = None
    parameter_name: Optional[str] = None
    previous_value: Any = None
    target_agent_id: Optional[int] = None
    amount: Optional[int] = None
    new_value: Any = None

class UndoStack:
    def __init__(self):
        self._stack: List[List[UndoRecord]] = []

    def start_batch(self):
        self._stack.append([])

    def push(self, record: UndoRecord):
        if not self._stack:
             self.start_batch()
        self._stack[-1].append(record)

    def pop_batch(self) -> List[UndoRecord]:
        if self._stack:
            return self._stack.pop()
        return []

class CommandService:
    def __init__(self, registry: IGlobalRegistry, settlement_system: ISettlementSystem, agent_registry: IAgentRegistry):
        self.registry = registry
        self.settlement_system = settlement_system
        self.agent_registry = agent_registry
        self.undo_stack = UndoStack()

    def dispatch_commands(self, commands: List[GodCommandDTO]) -> List[str]:
        results = []
        if not commands:
            return results

        self.undo_stack.start_batch()

        for cmd in commands:
            try:
                if cmd.command_type == "SET_PARAM":
                    self._handle_set_param(cmd)
                    results.append(f"SUCCESS: SET_PARAM {cmd.parameter_name} -> {cmd.new_value}")
                elif cmd.command_type == "INJECT_MONEY":
                    self._handle_inject_money(cmd)
                    results.append(f"SUCCESS: INJECT_MONEY {cmd.amount} to {cmd.target_agent_id}")
                else:
                    msg = f"ERROR: Unknown command type {cmd.command_type}"
                    logger.error(msg)
                    results.append(msg)
            except Exception as e:
                msg = f"ERROR: Execution failed for {cmd.command_type}: {e}"
                logger.error(msg, exc_info=True)
                results.append(msg)
                # Continue processing other commands as per spec
                continue

        return results

    def _handle_set_param(self, cmd: GodCommandDTO):
        if not cmd.parameter_name:
            raise ValueError("Parameter name missing for SET_PARAM")

        # Snapshot for Undo
        current_value = self.registry.get(cmd.parameter_name, None)

        record = UndoRecord(
            command_type="SET_PARAM",
            target_domain=cmd.target_domain,
            parameter_name=cmd.parameter_name,
            previous_value=current_value,
            new_value=cmd.new_value
        )
        self.undo_stack.push(record)

        # Execute
        # Assuming origin is GOD_MODE from DTO or use passed origin
        success = self.registry.set(cmd.parameter_name, cmd.new_value, origin=cmd.origin)
        if not success:
            raise RuntimeError(f"GlobalRegistry rejected update for {cmd.parameter_name}")

    def _handle_inject_money(self, cmd: GodCommandDTO):
        if cmd.target_agent_id is None or cmd.amount is None:
             raise ValueError("Target agent ID or amount missing for INJECT_MONEY")

        # Snapshot for Undo
        record = UndoRecord(
            command_type="INJECT_MONEY",
            target_agent_id=cmd.target_agent_id,
            amount=cmd.amount
        )

        # Execute
        success = self.settlement_system.mint_and_distribute(cmd.target_agent_id, cmd.amount, tick=0, reason="GodMode")
        if not success:
            raise RuntimeError(f"SettlementSystem failed to inject money to {cmd.target_agent_id}")

        # Push to stack only on success to avoid rollback of non-existent funds
        self.undo_stack.push(record)

    def commit_last_tick(self) -> None:
        """
        Commits the last batch of commands, removing them from the undo stack.
        This should be called when the tick is successfully validated (e.g., M2 audit passed).
        Prevents memory leaks from accumulating undo history.
        """
        self.undo_stack.pop_batch()

    def rollback_last_tick(self) -> bool:
        records = self.undo_stack.pop_batch()
        if not records:
            return False

        success = True
        # Reverse order for rollback
        for record in reversed(records):
            try:
                if record.command_type == "SET_PARAM":
                     # Restore previous value
                     # Using GOD_MODE origin to force revert
                     self.registry.set(record.parameter_name, record.previous_value, origin=OriginType.GOD_MODE)
                     logger.info(f"ROLLBACK: Reverted {record.parameter_name} to {record.previous_value}")

                elif record.command_type == "INJECT_MONEY":
                     self._rollback_injection(record)

            except Exception as e:
                logger.error(f"Rollback failed for {record}: {e}", exc_info=True)
                success = False

        return success

    def _rollback_injection(self, record: UndoRecord):
        target_agent = self.agent_registry.get_agent(record.target_agent_id)
        if not target_agent:
             raise RuntimeError(f"Target agent {record.target_agent_id} not found for rollback")

        central_bank = self.agent_registry.get_agent(ID_CENTRAL_BANK)
        if not central_bank:
             central_bank = self.agent_registry.get_agent(str(ID_CENTRAL_BANK))

        if not central_bank:
             raise RuntimeError("Central Bank not found for rollback")

        if not isinstance(target_agent, IFinancialAgent) or not isinstance(central_bank, IFinancialAgent):
             raise TypeError("Agents must be IFinancialAgent")

        # Execute rollback transfer (Target -> Central Bank) using transfer_and_destroy to burn
        tx = self.settlement_system.transfer_and_destroy(
            source=target_agent,
            sink_authority=central_bank,
            amount=record.amount,
            reason="GodMode_Rollback",
            tick=0
        )

        if not tx:
             raise RuntimeError(f"Failed to rollback injection of {record.amount} from {record.target_agent_id}")

        logger.info(f"ROLLBACK: Burned {record.amount} from {record.target_agent_id}")
