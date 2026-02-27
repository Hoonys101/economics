from _typeshed import Incomplete
from modules.governance.api import SetInterestRateCommand as SetInterestRateCommand, SetTaxRateCommand as SetTaxRateCommand, SystemCommand as SystemCommand, SystemCommandType as SystemCommandType
from modules.governance.cockpit.api import CockpitCommand as CockpitCommand, SetBaseRatePayload as SetBaseRatePayload, SetTaxRatePayload as SetTaxRatePayload
from modules.system.command_pipeline.api import CommandBatchDTO as CommandBatchDTO, ICommandIngressService as ICommandIngressService
from simulation.dtos.commands import GodCommandDTO

logger: Incomplete

class CommandIngressService:
    def __init__(self) -> None: ...
    def enqueue_command(self, command: CockpitCommand) -> None:
        """
        Maps CockpitCommand to internal DTOs and queues them.
        """
    def drain_for_tick(self, tick: int) -> CommandBatchDTO:
        """
        Atomically drains all queues and returns a CommandBatchDTO.
        """
    def drain_control_commands(self) -> list[GodCommandDTO]:
        """
        Drains pending Control commands.
        """
