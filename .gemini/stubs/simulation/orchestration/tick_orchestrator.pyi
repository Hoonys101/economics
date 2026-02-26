from _typeshed import Incomplete
from modules.system.api import DEFAULT_CURRENCY as DEFAULT_CURRENCY
from modules.system.command_pipeline.api import CommandBatchDTO as CommandBatchDTO, ICommandIngressService as ICommandIngressService
from modules.system.services.command_service import CommandService as CommandService
from simulation.action_processor import ActionProcessor as ActionProcessor
from simulation.dtos.api import GovernmentSensoryDTO as GovernmentSensoryDTO, SimulationState as SimulationState
from simulation.orchestration.api import IPhaseStrategy as IPhaseStrategy
from simulation.orchestration.phases import Phase0_PreSequence as Phase0_PreSequence, Phase1_Decision as Phase1_Decision, Phase2_Matching as Phase2_Matching, Phase3_Transaction as Phase3_Transaction, Phase5_PostSequence as Phase5_PostSequence, Phase_BankAndDebt as Phase_BankAndDebt, Phase_Bankruptcy as Phase_Bankruptcy, Phase_Consumption as Phase_Consumption, Phase_FirmProductionAndSalaries as Phase_FirmProductionAndSalaries, Phase_GovernmentPrograms as Phase_GovernmentPrograms, Phase_HousingSaga as Phase_HousingSaga, Phase_Production as Phase_Production, Phase_TaxationIntents as Phase_TaxationIntents
from simulation.orchestration.phases.god_commands import Phase_GodCommands as Phase_GodCommands
from simulation.orchestration.phases.metrics import Phase0_PreTickMetrics as Phase0_PreTickMetrics, Phase6_PostTickMetrics as Phase6_PostTickMetrics
from simulation.orchestration.phases.politics import Phase_Politics as Phase_Politics
from simulation.orchestration.phases.scenario_analysis import Phase_ScenarioAnalysis as Phase_ScenarioAnalysis
from simulation.orchestration.phases.system_commands import Phase_SystemCommands as Phase_SystemCommands
from simulation.orchestration.phases_recovery import Phase_SystemicLiquidation as Phase_SystemicLiquidation
from simulation.orchestration.utils import prepare_market_data as prepare_market_data
from simulation.world_state import WorldState as WorldState
from typing import Any

logger: Incomplete

class TickOrchestrator:
    world_state: Incomplete
    action_processor: Incomplete
    command_ingress: Incomplete
    command_service: Incomplete
    politics_system: Incomplete
    phases: list[IPhaseStrategy]
    def __init__(self, world_state: WorldState, action_processor: ActionProcessor, command_ingress: ICommandIngressService, command_service: CommandService) -> None: ...
    def run_tick(self, injectable_sensory_dto: GovernmentSensoryDTO | None = None) -> None: ...
    def prepare_market_data(self) -> dict[str, Any]:
        """
        Legacy/External access to market data preparation.
        """
