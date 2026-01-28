from __future__ import annotations
from typing import List, Dict, Any, Optional
import logging

from modules.common.config_manager.api import ConfigManager
from simulation.db.repository import SimulationRepository
from simulation.dtos import GovernmentStateDTO
from simulation.metrics.economic_tracker import EconomicIndicatorTracker
from simulation.systems.tech.api import FirmTechInfoDTO, HouseholdEducationDTO

from simulation.world_state import WorldState
from simulation.orchestration.tick_orchestrator import TickOrchestrator
from simulation.action_processor import ActionProcessor
from simulation.models import Transaction

logger = logging.getLogger(__name__)


class Simulation:
    """경제 시뮬레이션의 전체 흐름을 관리하고 조정하는 핵심 엔진 클래스. (Facade)"""

    def __init__(
        self,
        config_manager: ConfigManager,
        config_module: Any,
        logger: logging.Logger,
        repository: SimulationRepository
    ) -> None:
        """
        초기화된 구성 요소들을 할당받습니다.
        실제 생성 로직은 SimulationInitializer에 의해 외부에서 수행됩니다.
        """
        self.world_state = WorldState(
            config_manager=config_manager,
            config_module=config_module,
            logger=logger,
            repository=repository
        )
        self.action_processor = ActionProcessor(self.world_state)
        self.tick_orchestrator = TickOrchestrator(self.world_state, self.action_processor)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.world_state, name)

    def __setattr__(self, name: str, value: Any) -> None:
        # Avoid infinite recursion for internal components
        if name in ["world_state", "tick_orchestrator", "action_processor"]:
            super().__setattr__(name, value)
            return

        # Delegate to world_state if it has the attribute or if we are setting it dynamically
        if hasattr(self, "world_state"):
             setattr(self.world_state, name, value)
        else:
             super().__setattr__(name, value)

    def finalize_simulation(self):
        """시뮬레이션 종료 시 Repository 연결을 닫고, 시뮬레이션 종료 시간을 기록합니다."""
        if self.world_state.persistence_manager:
            self.world_state.persistence_manager.flush_buffers(self.world_state.time)
        
        self.world_state.repository.update_simulation_run_end_time(self.world_state.run_id)
        self.world_state.repository.close()
        self.world_state.logger.info("Simulation finalized and Repository connection closed.")

    def run_tick(self, injectable_sensory_dto: Optional[GovernmentStateDTO] = None) -> None:
        self.tick_orchestrator.run_tick(injectable_sensory_dto)

    def get_all_agents(self) -> List[Any]:
        """시뮬레이션에 참여하는 모든 활성 에이전트(가계, 기업, 은행 등)를 반환합니다."""
        return self.world_state.get_all_agents()

    # --- Backward Compatibility Methods ---

    def _prepare_market_data(self, tracker: EconomicIndicatorTracker) -> Dict[str, Any]:
        """Legacy wrapper for TickOrchestrator.prepare_market_data"""
        # Note: Tracker argument is ignored as orchestrator uses internal state
        return self.tick_orchestrator.prepare_market_data()

    def _calculate_total_money(self) -> float:
        """Legacy wrapper for WorldState.calculate_total_money"""
        return self.world_state.calculate_total_money()

    def _process_transactions(self, transactions: List[Transaction]) -> None:
        """Legacy wrapper for ActionProcessor.process_transactions"""
        # We need to reconstruct the callback.
        # Note: self.tracker comes from world_state via __getattr__
        market_data_cb = lambda: self._prepare_market_data(self.tracker).get("goods_market", {})
        self.action_processor.process_transactions(transactions, market_data_cb)

    def _process_stock_transactions(self, transactions: List[Transaction]) -> None:
        """Legacy wrapper for ActionProcessor.process_stock_transactions"""
        self.action_processor.process_stock_transactions(transactions)
