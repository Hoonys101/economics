from __future__ import annotations
from typing import List, Any, Optional, Protocol, Dict, Union, runtime_checkable
from dataclasses import dataclass, field
import logging
from uuid import UUID

from simulation.dtos.commands import GodCommandDTO, GodResponseDTO
from modules.system.api import IGlobalRegistry, OriginType, IAgentRegistry, RegistryEntry
from modules.system.constants import ID_CENTRAL_BANK
from simulation.finance.api import ISettlementSystem, IFinancialAgent
from modules.simulation.api import IInventoryHandler
from modules.finance.api import IBank
from collections import deque

logger = logging.getLogger(__name__)

class ICommandService(Protocol):
    def execute_command_batch(self, commands: List[GodCommandDTO], tick: int, baseline_m2: int) -> List[GodResponseDTO]:
        ...
    def commit_last_tick(self) -> None:
        ...

@runtime_checkable
class ISectorAgent(Protocol):
    sector: str

@dataclass
class UndoRecord:
    command_id: UUID
    command_type: str # "SET_PARAM" or "INJECT_ASSET"
    target_domain: Optional[str] = None
    parameter_key: Optional[str] = None
    previous_entry: Optional[RegistryEntry] = None # Changed from previous_value for full state restore
    target_agent_id: Optional[Union[int, str]] = None
    amount: Optional[int] = None
    new_value: Any = None

class UndoStack:
    def __init__(self, maxlen: int = 50):
        self._stack: deque = deque(maxlen=maxlen)
        self._current_batch: List[UndoRecord] = []

    def start_batch(self):
        self._current_batch = []

    def push(self, record: UndoRecord):
        self._current_batch.append(record)

    def commit_batch(self):
        if self._current_batch:
            self._stack.append(self._current_batch)
            self._current_batch = []

    def pop_batch(self) -> List[UndoRecord]:
        if self._current_batch:
            # If a batch is currently being built (e.g. during failure rollback), return it
            batch = self._current_batch
            self._current_batch = []
            return batch
        elif self._stack:
            return self._stack.pop()
        return []

class CommandService:
    def __init__(self, registry: IGlobalRegistry, settlement_system: ISettlementSystem, agent_registry: IAgentRegistry):
        self.registry = registry
        self.settlement_system = settlement_system
        self.agent_registry = agent_registry
        self.undo_stack = UndoStack()
        self._command_queue: deque = deque()

    def queue_command(self, command: GodCommandDTO) -> None:
        """Adds a command to the internal queue for later processing."""
        self._command_queue.append(command)

    def pop_commands(self) -> List[GodCommandDTO]:
        """Drains the internal command queue and returns the list of pending commands."""
        commands = list(self._command_queue)
        self._command_queue.clear()
        return commands

    def execute_command_batch(self, commands: List[GodCommandDTO], tick: int, baseline_m2: int) -> List[GodResponseDTO]:
        """
        Executes a batch of God-Mode commands with atomic rollback on audit failure.
        Lifecycle: Validation -> Snapshot -> Mutation -> Audit -> Commit/Rollback
        """
        results: List[GodResponseDTO] = []
        if not commands:
            return results

        self.undo_stack.start_batch()

        # Track net money injection for this batch
        net_injection = 0
        command_results: Dict[UUID, int] = {} # Map command_id to injected amount
        batch_success = True
        failure_reason = None
        executed_commands: List[GodCommandDTO] = []

        # 1. Validation, Snapshot, Mutation
        for cmd in commands:
            try:
                injected_amount = 0
                if cmd.command_type == "SET_PARAM":
                    self._handle_set_param(cmd)
                elif cmd.command_type == "INJECT_ASSET": # Spec compliant
                    injected_amount = self._handle_inject_asset(cmd, tick)
                    net_injection += injected_amount
                elif cmd.command_type == "INJECT_MONEY": # Legacy support
                    injected_amount = self._handle_inject_asset(cmd, tick) # Re-use logic
                    net_injection += injected_amount
                elif cmd.command_type == "UPDATE_TELEMETRY":
                    self._handle_update_telemetry(cmd)
                elif cmd.command_type == "TRIGGER_EVENT":
                    self._handle_trigger_event(cmd, tick)
                elif cmd.command_type == "PAUSE_STATE":
                    logger.info(f"Command {cmd.command_type} received but handler pending.")
                else:
                    logger.warning(f"Unknown command type: {cmd.command_type}")

                command_results[cmd.command_id] = injected_amount
                executed_commands.append(cmd)

            except Exception as e:
                logger.error(f"Execution failed for {cmd.command_id}: {e}", exc_info=True)
                batch_success = False
                failure_reason = str(e)
                # If one command fails, we should probably rollback the whole batch per atomicity requirement?
                # Spec says "Atomic Rollback". "integrity Check ... Rollback entire batch if any component fails".
                # So yes, break and rollback.
                break

        # 2. Audit (Financial Integrity)
        if batch_success:
            expected_total_m2 = baseline_m2 + net_injection
            audit_passed = self.settlement_system.audit_total_m2(expected_total=expected_total_m2)

            if not audit_passed:
                batch_success = False
                failure_reason = "M2 Integrity Audit Failed"
                logger.critical(f"AUDIT_FAIL | Expected M2: {expected_total_m2}. Triggering Rollback.")

        # 3. Commit or Rollback
        rollback_performed = False
        if not batch_success:
            rollback_performed = self.rollback_last_tick()
            if rollback_performed:
                logger.info("ROLLBACK_SUCCESS | Batch reversed.")
            else:
                logger.critical("ROLLBACK_FAIL | Batch reversal failed!")
        else:
            # Commit the batch (clear undo stack for this tick)
            self.commit_last_tick()

        # 4. Generate Responses
        for cmd in commands:
            # If the batch failed, all commands in it are considered failed/rolled back
            if not batch_success:
                results.append(GodResponseDTO(
                    command_id=cmd.command_id,
                    success=False,
                    execution_tick=tick,
                    failure_reason=failure_reason if failure_reason else "Batch execution failed",
                    rollback_performed=rollback_performed
                ))
            else:
                # Use individual command result for m2_delta
                m2_delta = command_results.get(cmd.command_id, 0)
                results.append(GodResponseDTO(
                    command_id=cmd.command_id,
                    success=True,
                    execution_tick=tick,
                    audit_report={"m2_delta": m2_delta}
                ))

        return results

    def _handle_set_param(self, cmd: GodCommandDTO):
        if not cmd.parameter_key:
            raise ValueError("Parameter key missing for SET_PARAM")

        # Snapshot for Undo
        # Use get_entry to capture full state (origin, is_locked)
        previous_entry = self.registry.get_entry(cmd.parameter_key)

        record = UndoRecord(
            command_id=cmd.command_id,
            command_type="SET_PARAM",
            target_domain=cmd.target_domain,
            parameter_key=cmd.parameter_key,
            previous_entry=previous_entry,
            new_value=cmd.new_value
        )
        self.undo_stack.push(record)

        # Execute
        # Assuming origin is GOD_MODE (from DTO property or similar)
        origin = getattr(cmd, 'origin', OriginType.GOD_MODE)
        success = self.registry.set(cmd.parameter_key, cmd.new_value, origin=origin)
        if not success:
            raise RuntimeError(f"GlobalRegistry rejected update for {cmd.parameter_key}")

    def _handle_inject_asset(self, cmd: GodCommandDTO, tick: int) -> int:
        # Map INJECT_ASSET to Money Injection logic
        # target_agent_id comes from parameter_key (e.g. "101")
        # amount comes from new_value (e.g. 1000)

        target_id_str = cmd.parameter_key
        amount = cmd.new_value

        # Helper/Legacy Accessors
        if hasattr(cmd, 'target_agent_id') and cmd.target_agent_id:
             target_id_str = cmd.target_agent_id
        if hasattr(cmd, 'amount') and cmd.amount is not None:
             amount = cmd.amount

        if not target_id_str:
             raise ValueError("Target agent ID missing for INJECT_ASSET")
        if amount is None or not isinstance(amount, int):
             raise ValueError("Amount must be an integer for INJECT_ASSET")

        # Resolve ID to int if possible, or keep string
        try:
            target_agent_id = int(target_id_str)
        except (ValueError, TypeError):
            target_agent_id = target_id_str # Keep as string if not int

        # Snapshot for Undo
        record = UndoRecord(
            command_id=cmd.command_id,
            command_type="INJECT_ASSET",
            target_agent_id=target_agent_id,
            amount=amount
        )

        # Execute
        success = self.settlement_system.mint_and_distribute(
            target_agent_id=target_agent_id,
            amount=amount,
            tick=tick,
            reason=f"GodMode_{cmd.command_id}"
        )
        if not success:
            raise RuntimeError(f"SettlementSystem failed to inject money to {target_agent_id}")

        # Push to stack only on success
        self.undo_stack.push(record)
        return amount

    def commit_last_tick(self) -> None:
        """
        Commits the last batch of commands.
        Modified for INT-02: We keep the history to allow manual UNDO (ST-004).
        Uses deque with maxlen to prevent memory leak.
        """
        self.undo_stack.commit_batch()

    def rollback_last_tick(self) -> bool:
        records = self.undo_stack.pop_batch()
        if not records:
            return True # Nothing to rollback is a success? Or implies failure to find batch?
                        # If called when nothing happened, it's fine.

        success = True
        # Reverse order for rollback
        for record in reversed(records):
            try:
                if record.command_type == "SET_PARAM":
                     # Restore previous entry state directly to preserve origin/locks
                     if record.previous_entry is None:
                         # Key didn't exist before, so delete it
                         # Access via protocol method delete_entry
                         if hasattr(self.registry, 'delete_entry'):
                             self.registry.delete_entry(record.parameter_key)
                             logger.info(f"ROLLBACK: Deleted {record.parameter_key}")
                         else:
                             # Should not happen if protocol is updated, but safe fallback logic
                             logger.warning(f"ROLLBACK_FAIL: delete_entry not implemented in registry for {record.parameter_key}")
                     else:
                         # Restore entry
                         if hasattr(self.registry, 'restore_entry'):
                             self.registry.restore_entry(record.parameter_key, record.previous_entry)
                             logger.info(f"ROLLBACK: Restored {record.parameter_key} to {record.previous_entry.value} (Origin: {record.previous_entry.origin})")
                         else:
                             # Fallback if restore_entry not available
                             self.registry.set(
                                 record.parameter_key,
                                 record.previous_entry.value,
                                 origin=record.previous_entry.origin
                             )
                             logger.warning(f"ROLLBACK: Used set() fallback for {record.parameter_key}. Lock state might be incorrect if mismatched.")

                elif record.command_type in ["INJECT_ASSET", "INJECT_MONEY"]:
                     self._rollback_injection(record)

            except Exception as e:
                logger.error(f"Rollback failed for {record}: {e}", exc_info=True)
                success = False

        return success

    def _rollback_injection(self, record: UndoRecord):
        target_agent = self.agent_registry.get_agent(record.target_agent_id)
        if not target_agent:
             # Try int casting if stored as string but registry uses int
             try:
                 target_agent = self.agent_registry.get_agent(int(record.target_agent_id))
             except:
                 pass

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

    def _handle_update_telemetry(self, cmd: GodCommandDTO):
        """
        Handles UPDATE_TELEMETRY command to change active subscriptions.
        """
        mask = cmd.new_value
        if not isinstance(mask, list):
            raise ValueError("New value for UPDATE_TELEMETRY must be a list of strings (mask).")

        # Access TelemetryCollector via GlobalRegistry (Initialized in initializer.py)
        # We need to access the 'system' origin or just get by key.
        collector = self.registry.get("system.telemetry_collector")

        if not collector:
            logger.error("TelemetryCollector not found in GlobalRegistry under 'system.telemetry_collector'")
            # Fallback or silent fail? Better to raise error so command reports failure.
            raise RuntimeError("TelemetryCollector service is not available.")

        if hasattr(collector, "update_subscriptions"):
            collector.update_subscriptions(mask)
            logger.info(f"Telemetry mask updated: {mask}")
        else:
            raise RuntimeError("TelemetryCollector does not support 'update_subscriptions'.")

    def _handle_trigger_event(self, cmd: GodCommandDTO, tick: int):
        """
        Handles TRIGGER_EVENT commands like FORCE_WITHDRAW_ALL and DESTROY_INVENTORY.
        """
        event_type = cmd.parameter_key
        logger.info(f"TRIGGER_EVENT: {event_type} initiated.")

        if event_type == "FORCE_WITHDRAW_ALL":
            self._handle_force_withdraw_all(cmd, tick)
        elif event_type == "DESTROY_INVENTORY":
            self._handle_destroy_inventory(cmd, tick)
        else:
            logger.warning(f"Unknown event type: {event_type}")

    def _handle_force_withdraw_all(self, cmd: GodCommandDTO, tick: int):
        """
        Simulates a systemic bank run by forcing all agents to withdraw their deposits.
        """
        # Identify Target Bank
        # Default to finding any IBank if not specified or "CENTRAL" (which might mean Central Clearing)
        # But usually we want the Commercial Bank where agents have deposits.

        bank_id_target = None
        if isinstance(cmd.new_value, dict):
            bank_id_target = cmd.new_value.get("bank_id")

        # Find the Bank Agent
        bank_agent = None
        if bank_id_target and bank_id_target != "CENTRAL":
             bank_agent = self.agent_registry.get_agent(bank_id_target)

        if not bank_agent:
             # Heuristic: Find the first commercial bank
             all_agents = self.agent_registry.get_all_agents()
             for agent in all_agents:
                 if isinstance(agent, IBank) and agent.id != ID_CENTRAL_BANK and str(agent.id) != str(ID_CENTRAL_BANK):
                     bank_agent = agent
                     break

        if not bank_agent:
             logger.warning("FORCE_WITHDRAW_ALL: No suitable commercial bank found.")
             return

        if not isinstance(bank_agent, IBank):
             logger.warning(f"FORCE_WITHDRAW_ALL: Target {bank_agent.id} is not an IBank.")
             return

        logger.info(f"FORCE_WITHDRAW_ALL: Targeting Bank {bank_agent.id}")

        # Iterate all agents and withdraw
        agents = self.agent_registry.get_all_agents()
        withdrawal_count = 0
        total_withdrawn = 0

        for agent in agents:
            # Skip the bank itself and central bank
            if agent.id == bank_agent.id or agent.id == ID_CENTRAL_BANK:
                continue

            # Check Balance
            # Since IBank doesn't expose get_balance_of(agent), we use seamless withdraw check or custom method
            # Bank.get_customer_balance is available in the implementation we read earlier
            # Check Balance
            # Since IBank doesn't expose get_balance_of(agent), we use seamless withdraw check or custom method
            if isinstance(bank_agent, IBank): # Protocol check
                 balance = bank_agent.get_customer_balance(agent.id)
                 if balance > 0:
                     # Execute Withdrawal - Two-Step Process for Zero-Sum Integrity

                     # 1. Reduce Bank Liability (Deposit)
                     liability_reduced = bank_agent.withdraw_for_customer(agent.id, balance)

                     if liability_reduced:
                         # 2. Transfer Cash (Bank Asset -> Agent Asset)
                         # This ensures the Bank loses cash reserves corresponding to the liability reduction.
                         tx = self.settlement_system.transfer(
                             debit_agent=bank_agent,
                             credit_agent=agent,
                             amount=balance,
                             memo="FORCE_WITHDRAW_ALL",
                             tick=tick
                         )

                         if tx:
                             total_withdrawn += balance
                             withdrawal_count += 1
                         else:
                             # Rollback Liability Reduction if Cash Transfer fails (e.g. Bank Insolvent)
                             logger.warning(f"Bank {bank_agent.id} insolvent! Failed to transfer cash {balance} to {agent.id}. Rolling back liability.")
                             # Try to restore deposit (Legacy method usually available on Bank implementation)
                             if hasattr(bank_agent, 'deposit_from_customer'):
                                 bank_agent.deposit_from_customer(agent.id, float(balance))
                     else:
                         logger.warning(f"Failed to reduce liability {balance} for agent {agent.id}")

        logger.info(f"FORCE_WITHDRAW_ALL: Processed {withdrawal_count} withdrawals. Total: {total_withdrawn}")

    def _handle_destroy_inventory(self, cmd: GodCommandDTO, tick: int):
        """
        Destroys inventory across firms to simulate disaster (War/Famine).
        """
        ratio = 0.9 # Default
        target_sector = None

        if isinstance(cmd.new_value, dict):
            ratio = cmd.new_value.get("ratio", 0.9)
            target_sector = cmd.new_value.get("target")
        elif isinstance(cmd.new_value, (float, int)):
             ratio = float(cmd.new_value)

        agents = self.agent_registry.get_all_agents()
        destroyed_value_estimate = 0
        agents_affected = 0

        for agent in agents:
            if isinstance(agent, IInventoryHandler):
                # Filter by sector if needed (only Firms have sector usually)
                if target_sector:
                     # Protocol Check for Sector
                     if not isinstance(agent, ISectorAgent) or agent.sector != target_sector:
                         continue

                items = agent.get_all_items()
                for item_id, qty in list(items.items()):
                    destroy_qty = qty * ratio
                    if destroy_qty > 0:
                        success = agent.remove_item(item_id, destroy_qty)
                        if success:
                             # Rough estimate of value (assuming 1.0 unit price if unknown, just for logging)
                             destroyed_value_estimate += destroy_qty

                agents_affected += 1

        logger.info(f"DESTROY_INVENTORY: Affected {agents_affected} agents. Destroyed approx {destroyed_value_estimate} units.")
