from enum import Enum
from modules.government.api import IGovernment as IGovernment
from pydantic import BaseModel, Field as Field
from simulation.dtos.api import SimulationState as SimulationState
from typing import Literal, Protocol

class SystemCommandType(str, Enum):
    """Defines the types of available system-level manual interventions."""
    SET_TAX_RATE = 'SET_TAX_RATE'
    SET_INTEREST_RATE = 'SET_INTEREST_RATE'

class BaseSystemCommand(BaseModel):
    """Base structure for all system commands."""
    command_type: SystemCommandType

class SetTaxRateCommand(BaseSystemCommand):
    """Command to set a specific tax rate for the government."""
    command_type: Literal[SystemCommandType.SET_TAX_RATE]
    tax_type: Literal['corporate', 'income']
    new_rate: float

class SetInterestRateCommand(BaseSystemCommand):
    """Command to set a specific interest rate for the central bank."""
    command_type: Literal[SystemCommandType.SET_INTEREST_RATE]
    rate_type: Literal['base_rate']
    new_rate: float
SystemCommand = SetTaxRateCommand | SetInterestRateCommand

class IFiscalPolicyHolder(Protocol):
    corporate_tax_rate: float
    income_tax_rate: float

class ICentralBank(Protocol):
    base_rate: float

class ISystemCommandHandler(Protocol):
    """
    Interface for a processor that handles the execution of system commands.
    This will be implemented by the SystemCommandProcessor.
    """
    def execute(self, command: SystemCommand, state: SimulationState) -> SimulationState:
        """
        Executes a given command, modifying and returning the simulation state.

        Args:
            command: The command DTO to execute.
            state: The current simulation state DTO.

        Returns:
            The modified simulation state DTO.
        """
