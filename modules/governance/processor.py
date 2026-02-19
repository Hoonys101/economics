from __future__ import annotations
from typing import TYPE_CHECKING, cast
import logging
from typing import Protocol, runtime_checkable

from modules.governance.api import (
    ISystemCommandHandler, SystemCommand, SystemCommandType, SetTaxRateCommand, SetInterestRateCommand,
    IGovernment, ICentralBank
)

if TYPE_CHECKING:
    from simulation.dtos.api import SimulationState

logger = logging.getLogger(__name__)

class SystemCommandProcessor(ISystemCommandHandler):
    """
    Processes system-level commands to manually intervene in the simulation state.
    """

    def execute(self, command: SystemCommand, state: SimulationState) -> SimulationState:
        """
        Executes a given command, modifying and returning the simulation state.
        """
        # Pydantic Model access
        cmd_type = command.command_type

        logger.info(
            f"SYSTEM_COMMAND | Executing {cmd_type.name}",
            extra={"tick": state.time, "command": command.model_dump()}
        )

        if cmd_type == SystemCommandType.SET_TAX_RATE:
            # We cast for type checker, runtime assumes correct structure based on enum
            self._handle_set_tax_rate(cast(SetTaxRateCommand, command), state)
        elif cmd_type == SystemCommandType.SET_INTEREST_RATE:
            self._handle_set_interest_rate(cast(SetInterestRateCommand, command), state)
        else:
            logger.warning(f"SYSTEM_COMMAND | Unknown command type: {cmd_type}")

        return state

    def _handle_set_tax_rate(self, command: SetTaxRateCommand, state: SimulationState):
        tax_type = command.tax_type
        new_rate = command.new_rate

        if state.government is None:
            logger.error("SYSTEM_COMMAND | Government agent is None.")
            return

        # Guardrail: Strict Protocol Compliance Check
        if not isinstance(state.government, IGovernment):
            logger.error(f"SYSTEM_COMMAND | Government agent {type(state.government)} does not satisfy IGovernment protocol.")
            return

        government = state.government

        if tax_type == 'corporate':
            old_rate = government.corporate_tax_rate
            government.corporate_tax_rate = new_rate

            # Protocol IGovernment defines fiscal_policy as IFiscalPolicyHolder
            if government.fiscal_policy:
                government.fiscal_policy.corporate_tax_rate = new_rate

            logger.info(f"SYSTEM_COMMAND | Corporate Tax Rate: {old_rate} -> {new_rate}")

        elif tax_type == 'income':
            old_rate = government.income_tax_rate
            government.income_tax_rate = new_rate

            if government.fiscal_policy:
                government.fiscal_policy.income_tax_rate = new_rate

            logger.info(f"SYSTEM_COMMAND | Income Tax Rate: {old_rate} -> {new_rate}")

        else:
            logger.warning(f"SYSTEM_COMMAND | Unknown tax type: {tax_type}")

    def _handle_set_interest_rate(self, command: SetInterestRateCommand, state: SimulationState):
        rate_type = command.rate_type
        new_rate = command.new_rate

        if state.central_bank is None:
            logger.error("SYSTEM_COMMAND | Central Bank agent is None.")
            return

        # Guardrail: Strict Protocol Compliance Check
        if not isinstance(state.central_bank, ICentralBank):
             logger.error(f"SYSTEM_COMMAND | Central Bank agent {type(state.central_bank)} does not satisfy ICentralBank protocol.")
             return

        central_bank = state.central_bank

        if rate_type == 'base_rate':
            old_rate = central_bank.base_rate
            central_bank.base_rate = new_rate
            logger.info(f"SYSTEM_COMMAND | CB Base Rate: {old_rate} -> {new_rate}")
        else:
            logger.warning(f"SYSTEM_COMMAND | Unknown interest rate type: {rate_type}")
