import logging
from _typeshed import Incomplete
from modules.common.config_manager.api import ConfigManager as ConfigManager
from modules.finance.api import ISettlementSystem as ISettlementSystem
from modules.simulation.api import EconomicIndicatorsDTO, SystemStateDTO
from modules.system.api import IAgentRegistry as IAgentRegistry, IGlobalRegistry as IGlobalRegistry
from modules.system.command_pipeline.api import ICommandIngressService as ICommandIngressService
from modules.system.services.command_service import CommandService as CommandService
from simulation.action_processor import ActionProcessor as ActionProcessor
from simulation.db.db_manager import DBManager as DBManager
from simulation.db.logger import SimulationLogger as SimulationLogger
from simulation.db.repository import SimulationRepository as SimulationRepository
from simulation.dtos import GovernmentSensoryDTO as GovernmentSensoryDTO
from simulation.dtos.commands import GodCommandDTO as GodCommandDTO
from simulation.metrics.economic_tracker import EconomicIndicatorTracker as EconomicIndicatorTracker
from simulation.models import Transaction as Transaction
from simulation.orchestration.tick_orchestrator import TickOrchestrator as TickOrchestrator
from simulation.systems.tech.api import FirmTechInfoDTO as FirmTechInfoDTO, HouseholdEducationDTO as HouseholdEducationDTO
from simulation.world_state import WorldState as WorldState
from typing import Any

logger: Incomplete

class Simulation:
    """경제 시뮬레이션의 전체 흐름을 관리하고 조정하는 핵심 엔진 클래스. (Facade)"""
    world_state: Incomplete
    agent_registry: Incomplete
    settlement_system: Incomplete
    command_service: Incomplete
    command_ingress: Incomplete
    action_processor: Incomplete
    tick_orchestrator: Incomplete
    simulation_logger: SimulationLogger
    db_manager: Incomplete
    def __init__(self, config_manager: ConfigManager, config_module: Any, logger: logging.Logger, repository: SimulationRepository, registry: IGlobalRegistry, settlement_system: ISettlementSystem, agent_registry: IAgentRegistry, command_service: CommandService, command_ingress: ICommandIngressService | None = None) -> None:
        """
        초기화된 구성 요소들을 할당받습니다.
        실제 생성 로직은 SimulationInitializer에 의해 외부에서 수행됩니다.
        """
    def initialize(self) -> None:
        """
        Final initialization step for the Simulation facade.
        Ensures the database schema is up-to-date before any processing begins.
        """
    @property
    def is_paused(self) -> bool: ...
    @is_paused.setter
    def is_paused(self, value: bool) -> None: ...
    @property
    def step_requested(self) -> bool: ...
    @step_requested.setter
    def step_requested(self, value: bool) -> None: ...
    def __getattr__(self, name: str) -> Any: ...
    def __setattr__(self, name: str, value: Any) -> None: ...
    def finalize_simulation(self) -> None:
        """시뮬레이션 종료 시 Repository 연결을 닫고, 시뮬레이션 종료 시간을 기록합니다."""
    def run_tick(self, injectable_sensory_dto: GovernmentSensoryDTO | None = None) -> None: ...
    def get_all_agents(self) -> list[Any]:
        """시뮬레이션에 참여하는 모든 활성 에이전트(가계, 기업, 은행 등)를 반환합니다."""
    def get_economic_indicators(self) -> EconomicIndicatorsDTO:
        """
        Retrieves the current market snapshot containing economic indicators.
        Exposes a public interface for observers (satisfies ISimulationState).
        Formerly get_market_snapshot.
        """
    def get_system_state(self) -> SystemStateDTO:
        """
        Retrieves internal system state for phenomena analysis.
        Implements ISimulationState.get_system_state.
        """
