from __future__ import annotations
import logging
from collections import deque
from typing import List, Any
from simulation.dtos.commands import GodCommandDTO
from modules.governance.api import SystemCommand, SetTaxRateCommand, SetInterestRateCommand, SystemCommandType
from modules.governance.cockpit.api import CockpitCommand, SetTaxRatePayload, SetBaseRatePayload
from modules.system.command_pipeline.api import ICommandIngressService, CommandBatchDTO

logger = logging.getLogger(__name__)

class CommandIngressService:
    def __init__(self):
        self._command_queue: deque = deque()
        self._system_command_queue: deque = deque()
        self._control_queue: deque = deque()

    def enqueue_command(self, command: CockpitCommand) -> None:
        """
        Maps CockpitCommand to internal DTOs and queues them.
        """
        logger.info(f"CommandIngressService received CockpitCommand: {command.type}")

        if command.type == "PAUSE":
             self._control_queue.append(GodCommandDTO(
                 target_domain="System",
                 parameter_key="PAUSE_STATE",
                 new_value=True,
                 command_type="PAUSE_STATE"
             ))
        elif command.type == "RESUME":
             self._control_queue.append(GodCommandDTO(
                 target_domain="System",
                 parameter_key="PAUSE_STATE",
                 new_value=False,
                 command_type="PAUSE_STATE"
             ))
        elif command.type == "STEP":
             self._control_queue.append(GodCommandDTO(
                 target_domain="System",
                 parameter_key="STEP",
                 new_value=None,
                 command_type="TRIGGER_EVENT"
             ))
        elif command.type == "SET_TAX_RATE":
             try:
                 payload_dto = SetTaxRatePayload(**command.payload)
                 sys_cmd = SetTaxRateCommand(
                     tax_type=payload_dto.tax_type,
                     new_rate=payload_dto.rate
                 )
                 self._system_command_queue.append(sys_cmd)
             except Exception as e:
                 logger.error(f"Failed to map SET_TAX_RATE: {e}")

        elif command.type == "SET_BASE_RATE":
             try:
                 payload_dto = SetBaseRatePayload(**command.payload)
                 sys_cmd = SetInterestRateCommand(
                     rate_type="base_rate",
                     new_rate=payload_dto.rate
                 )
                 self._system_command_queue.append(sys_cmd)
             except Exception as e:
                 logger.error(f"Failed to map SET_BASE_RATE: {e}")
        else:
            logger.warning(f"Unknown CockpitCommand type: {command.type}")

    def drain_for_tick(self, tick: int) -> CommandBatchDTO:
        """
        Atomically drains all queues and returns a CommandBatchDTO.
        """
        god_commands = []
        while self._command_queue:
            god_commands.append(self._command_queue.popleft())

        system_commands = []
        while self._system_command_queue:
            system_commands.append(self._system_command_queue.popleft())

        return CommandBatchDTO(
            tick=tick,
            god_commands=god_commands,
            system_commands=system_commands
        )

    def drain_control_commands(self) -> List[GodCommandDTO]:
        """
        Drains pending Control commands.
        """
        commands = []
        while self._control_queue:
            commands.append(self._control_queue.popleft())
        return commands
