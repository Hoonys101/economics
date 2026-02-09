from __future__ import annotations
import logging
from collections import deque
from typing import List, Deque, Optional, Any, Dict
from modules.governance.cockpit.api import CockpitCommand, ICommandService, CockpitCommandType

logger = logging.getLogger(__name__)

class CommandService:
    """
    Manages the queue of commands received from the Cockpit.
    Thread-safe due to deque's atomic operations for append/popleft in CPython,
    though explicit locking might be needed for strict guarantees in some environments.
    For this simulation loop (async server -> sync simulation), it relies on the fact
    that the simulation runs in a separate thread but processes commands at a specific point.
    """

    def __init__(self):
        self._command_queue: Deque[CockpitCommand] = deque()

    def validate_command(self, command: CockpitCommand) -> bool:
        """
        Validates the command payload based on its type.
        """
        try:
            if command.type == "SET_BASE_RATE":
                rate = command.payload.get("rate")
                if not isinstance(rate, (int, float)):
                    logger.warning(f"Invalid rate type for SET_BASE_RATE: {type(rate)}")
                    return False
                if not (0.0 <= rate <= 0.2):
                    logger.warning(f"Rate out of bounds for SET_BASE_RATE: {rate} (Expected 0.0-0.2)")
                    return False
                return True

            elif command.type == "SET_TAX_RATE":
                tax_type = command.payload.get("tax_type")
                rate = command.payload.get("rate")

                if tax_type not in ["corporate", "income"]:
                    logger.warning(f"Invalid tax_type for SET_TAX_RATE: {tax_type}")
                    return False

                if not isinstance(rate, (int, float)):
                    logger.warning(f"Invalid rate type for SET_TAX_RATE: {type(rate)}")
                    return False

                if not (0.0 <= rate <= 1.0):
                    logger.warning(f"Rate out of bounds for SET_TAX_RATE: {rate} (Expected 0.0-1.0)")
                    return False
                return True

            elif command.type in ["PAUSE", "RESUME", "STEP"]:
                # These commands have no payload requirements
                return True

            else:
                logger.warning(f"Unknown command type: {command.type}")
                return False

        except Exception as e:
            logger.error(f"Error validating command {command}: {e}")
            return False

    def enqueue_command(self, command: CockpitCommand) -> None:
        """
        Adds a command to the queue if valid.
        """
        if self.validate_command(command):
            self._command_queue.append(command)
            logger.info(f"Command enqueued: {command.type} | Payload: {command.payload}")
        else:
            logger.warning(f"Command rejected due to validation failure: {command}")

    def pop_commands(self) -> List[CockpitCommand]:
        """
        Returns all pending commands and clears the queue.
        """
        commands = []
        try:
            while self._command_queue:
                commands.append(self._command_queue.popleft())
        except IndexError:
            pass # Queue became empty during iteration (unlikely with single consumer)
        return commands
